import requests
import time
import json
import threading
from pprint import pprint

# ================================ 用户配置指南 (必读) ================================
#
# 您需要通过浏览器的F12开发者工具来获取以下所有信息。
# 脚本支持两种模式, 启动后会先询问您本次抢的是本科课还是研究生课:
#
#   - 本科模式: 选课系统支持一次保存多门课, 所有课程共用一对 ciphertext/checkCode,
#               需要填写目标课程的 teachClassId 列表, 全部选上后脚本自动退出。
#   - 研究生模式: 选课系统一次只能保存一门课, 因此需要为每一门课单独抓包,
#               获取一对 ciphertext/checkCode。脚本会并发模拟多个"网页"同时抢课,
#               每个线程负责一门课, 对应课程抢到后该线程自动退出。
#
# --- Part 1: 获取身份与选课凭证 (两种模式通用) ---
#   1. 登录选课系统, 打开F12开发者工具, 切换到 "Network" (网络) 选项卡。
#   2. 在页面上进行一次"保存课表"的操作。
#   3. 在F12的网络请求列表中, 找到一个名为 "elect" 的请求, 点击它。
#
#   - ToDo 1: 获取 X-Token
#     在 "elect" 请求的 "Headers" (请求头) 部分, 找到 "X-Token" 字段, 复制其值, 若无该字段则具体方法详见README。
#
#   - ToDo 2: 获取 ciphertext 和 checkCode
#     在 "elect" 请求的 "Payload" (载荷) 部分, 找到并复制 "ciphertext" 和 "checkCode" 的值。
#     [研究生注意] 由于一次只能保存一门课, 每门课都要单独勾选后点一次"保存课表",
#     分别抓取一对 ciphertext/checkCode (见 ToDo 4)。
#
# --- Part 2: 获取课程的内部ID (teachClassId) ---
#   [本科必填]
#   1. 仍在F12的 "Network" 选项卡。
#   2. 将选课的"结果"关闭（注意要点击弹窗的下面的关闭按钮而不是直接点右上角的"×"）。
#   3. 在网络请求列表中, 找到一个返回了大量课程信息的JSON文件。
#      (这个请求的名字可能是以getTeachClass4Limit?为开头的一长串url请求)
#   4. 点击这个请求, 查看其 "Response" (响应) 或 "Preview" (预览)。
#
#   - ToDo 3: 获取 teachClassId
#     在搜索到的课程信息中, 找到 "teachClassId" 字段, 复制它的值 (是一长串以1111...开头的数字)。
#     为您想抢的每一门课都重复此操作。（注意同一门课的不同时间段有不同的teachClassId,请对照您要抢的时间段的课程序号与teachClassCode字段的值是否对应）
#
#   [研究生：多课必填，单课建议填写]
#   研究生课程的 teachClassId 可以在 F12 -> Network 中的 "getData" 请求的响应里找到。
#   由于研究生模式下每对凭证已经和具体课程一一绑定, 单课可以不填，多课必须填写;
#   如果并发抢多门课, 必须填写(见 ToDo 4), 以便脚本精确判断是哪门课抢到了,
#   避免一个线程把别的线程的战果误认成自己的。
#
# ================================ 用户配置区域 (请将抓取的值填入下方) ================================

# ToDo 1: 填入您的 X-Token (两种模式通用)
headers = {
    "X-Token": "在这里替换成你自己的X-Token",
}

# ---------- 本科模式配置 ----------

# ToDo 2: 填入您的 ciphertext 和 checkCode (本科: 一次保存可提交多门课, 全部课程共用一对)
undergrad_data = {"ciphertext": "在这里替换成你自己的ciphertext", 
                  "checkCode": "在这里替换成你自己的checkCode"}

# ToDo 3: 填入您想抢的所有课程的【teachClassId】列表 (仅本科模式需要)
# 例如: targetCourseIds = [1111111124934476, 1111111124934261]
targetCourseIds = []

# ---------- 研究生模式配置 ----------

# ToDo 4: 为每一门想抢的课程填写一组 (课程备注, ciphertext, checkCode)
# 研究生选课系统一次只能保存一门课, 因此每门课需要单独抓包获取一对凭证。
# 第4个元素 teachClassId 为【多课必填，单课可选】(用于精确判断该门课是否抢到, 可在 getData 请求响应中找到):
#   - 不填: 仅限单课兼容模式，无法按目标 ID 核验成功记录;
#   - 填写: 仅当成功课程与该 teachClassId 匹配时才退出, 并发抢多门课时必须填写。
# 例如:
# 以下教学班 ID 仅为格式示例，请替换成各自课程的真实 ID。
# grad_requests = [
#     ("机器学习", "在这里替换成课程1的ciphertext", "在这里替换成课程1的checkCode", 1111111124000001),
#     ("中国马克思主义与当代", "在这里替换成课程2的ciphertext", "在这里替换成课程2的checkCode", 1111111124000002),
# ]
grad_requests = []

# (可选) 请求间隔, 单位秒
interval = 3

# ================================ 脚本主逻辑区 (无需修改) ================================

rqstUrl = "https://1.tongji.edu.cn/api/electionservice/student/elect"
statusUrl = "https://1.tongji.edu.cn/api/electionservice/student/5435/electRes"
SESSION_NOT_EXIST = '{"message":"sessionid is not exist."}'


def extract_success_ids(successes):
    """兼容 successCourses 为 id 列表或 dict 列表两种返回格式, 统一提取出数字 id 集合。"""
    ids = set()
    for c in successes:
        v = c.get("teachClassId", c.get("courseId")) if isinstance(c, dict) else c
        try:
            ids.add(int(v))
        except (TypeError, ValueError):
            pass
    return ids


# ================================ 本科模式 ================================

def run_undergraduate():
    # 检查配置是否完整
    if "替换" in undergrad_data["ciphertext"] or "替换" in undergrad_data["checkCode"]:
        print("错误: 本科模式的 ciphertext 或 checkCode 未填写，请检查脚本配置！")
        exit()
    if not targetCourseIds:
        print("错误: 目标课程ID列表 (targetCourseIds) 为空，请按照说明填写课程的【teachClassId】！")
        exit()

    print("正在核验Token和选课信息有效性...")
    try:
        response1 = requests.post(rqstUrl, json=undergrad_data, headers=headers)
        if response1.text == SESSION_NOT_EXIST:
            print("选课会話不存在, 请检查X-Token输入是否正确或过期...")
            exit()
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败，请检查网络连接或API地址: {e}")
        exit()

    print("选课信息有效, 开始自动选课...")
    print(f"监控的目标 teachClassId: {targetCourseIds}")
    print(f"抢课间隔时间： {interval} 秒...")

    tryCount = 0
    successList = set()
    targetSet = set(targetCourseIds)

    while not targetSet.issubset(successList):
        tryCount += 1
        print("\n+===================================================================================+")
        print(f"第 {tryCount} 次尝试: ")

        try:
            requests.post(rqstUrl, json=undergrad_data, headers=headers)
            print("已发送选课请求, 等待查询选课结果...")
            time.sleep(interval)

            response_status = requests.post(statusUrl, headers=headers)
            status_data = response_status.json()

            if status_data and "data" in status_data and "successCourses" in status_data["data"]:
                returned_ids = status_data["data"]["successCourses"]
                if returned_ids:
                    print(" 有课程选课成功! 返回的 teachClassId 如下: ")
                    pprint(returned_ids)
                    for course_id in extract_success_ids(returned_ids):
                        successList.add(course_id)
                else:
                    print("本次尝试没有新增的成功课程...")

                if "failedReasons" in status_data["data"] and status_data["data"]["failedReasons"]:
                    print("有课程选课失败! 失败原因汇总如下: ")
                    pprint(status_data["data"]["failedReasons"])
            else:
                print("服务器响应格式异常，未找到成功课程列表。")
                pprint(status_data)

        except requests.exceptions.RequestException as e:
            print(f"发生网络错误: {e}")
        except json.JSONDecodeError:
            print(f"服务器响应不是有效的JSON格式: {response_status.text}")
        except Exception as e:
            print(f"发生未知错误: {e}")

        if targetSet.issubset(successList):
            print("\n+===================================================================================+")
            print(" 恭喜！所有目标课程都已选上！")
            print("最终成功选课的 teachClassId: ")
            pprint(list(successList))
            print("脚本执行完毕，自动退出。")
            break
        else:
            remaining_courses = targetSet - successList
            print("\n--- 当前进度 ---")
            print(f"已成功 teachClassId: {list(successList)}")
            print(f"还需努力的 teachClassId: {list(remaining_courses)}")

            time.sleep(interval)


# ================================ 研究生模式 ================================

def normalize_grad_requests(entries):
    """在任何网络请求之前校验并规范化配置。多课必须能够按 ID 归属结果。"""
    normalized = []
    labels, ids = set(), set()
    if not entries:
        raise ValueError("研究生目标课程列表为空。")
    for entry in entries:
        if not isinstance(entry, (list, tuple)) or len(entry) not in (3, 4):
            raise ValueError("每门课须填写 (备注, ciphertext, checkCode[, teachClassId])。")
        label, ct, cc = entry[:3]
        if not all(isinstance(v, str) and v.strip() for v in (label, ct, cc)):
            raise ValueError("课程备注与凭证不能为空。")
        if label in labels:
            raise ValueError("课程备注不能重复，请为不同教学班设置不同备注。")
        labels.add(label)
        value = entry[3] if len(entry) == 4 else None
        if value is None or (isinstance(value, str) and not value.strip()):
            if len(entries) > 1:
                raise ValueError("研究生同时选多门课时，每门课都必须填写 teachClassId；否则无法区分共享查询结果。")
            normalized.append((label, ct, cc))
            continue
        if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).strip().isdigit() or int(value) <= 0:
            raise ValueError("teachClassId 必须是正整数或仅含数字的字符串。")
        teach_id = int(value)
        if teach_id in ids:
            raise ValueError("teachClassId 重复，请检查是否为同一个教学班配置了多个任务。")
        ids.add(teach_id)
        normalized.append((label, ct, cc, teach_id))
    return normalized


def grad_worker(entry, success_set, lock, stop_event):
    """一个线程 = 一个模拟的"网页", 负责抢一门课, 抢到后自动退出。

    entry 格式: (课程备注, ciphertext, checkCode[, 可选 teachClassId])
    """
    label = entry[0]
    ciphertext, checkCode = entry[1], entry[2]
    teach_id = int(entry[3]) if len(entry) >= 4 and entry[3] is not None else None
    tag = f"[{label}]"

    session = requests.Session()
    session.headers.update(headers)

    tryCount = 0
    while not stop_event.is_set():
        tryCount += 1
        try:
            with lock:
                print(f"{tag} 第 {tryCount} 次尝试: 发送选课请求, 等待查询选课结果...")
            r = session.post(rqstUrl, json={"ciphertext": ciphertext, "checkCode": checkCode})
            if r.text == SESSION_NOT_EXIST:
                with lock:
                    print(f"{tag} 选课会话不存在, 请检查X-Token输入是否正确或过期...")
                stop_event.set()
                return
            if r.text.strip():
                with lock:
                    print(f"{tag} 选课接口响应: {r.text[:200]}")
            time.sleep(interval)

            rs = session.post(statusUrl)
            if rs.text == SESSION_NOT_EXIST:
                with lock:
                    print(f"{tag} 查询时会话已失效，请重新获取 X-Token。")
                stop_event.set()
                return
            status_data = rs.json()
            data = (status_data or {}).get("data") or {}
            successes = data.get("successCourses") or []
            failures = data.get("failedReasons") or []

            if failures:
                with lock:
                    print(f"{tag} 有课程选课失败! 失败原因汇总如下: ")
                    pprint(failures)

            # ---- 判断本线程的目标课程是否抢到 ----
            if successes and data.get("status") == "Ready":
                if teach_id is not None:
                    if teach_id in extract_success_ids(successes):
                        with lock:
                            print(f"{tag} 恭喜! 目标课程选课成功!")
                            pprint(successes)
                        with lock:
                            success_set.add(label)
                        return
                    # 成功的是别的线程的课, 本线程继续努力
                else:
                    # 仅允许单课兼容模式；多课缺少 ID 已由启动校验拒绝。
                    with lock:
                        print(f"{tag} 单课兼容模式：检测到成功记录，尚未按目标 ID 核验，请到网页确认。")
                        pprint(successes)
                    with lock:
                        success_set.add(label)
                    return

        except requests.exceptions.RequestException as e:
            with lock:
                print(f"{tag} 发生网络错误: {e}")
        except json.JSONDecodeError as e:
            with lock:
                print(f"{tag} 服务器响应不是有效的JSON格式: {e}")
        except Exception as e:
            with lock:
                print(f"{tag} 发生未知错误: {e}")

        stop_event.wait(interval)


def run_graduate():
    try:
        entries = normalize_grad_requests(grad_requests)
    except ValueError as e:
        print(f"配置错误：{e}")
        return
    if len(entries[0]) == 3:
        print("提示：单课未填 teachClassId，只能使用兼容判断；建议填写 ID，并避免同时在网页提交其他课程。")
    success_set = set()
    lock = threading.Lock()
    stop_event = threading.Event()

    print(f"研究生模式: 共 {len(grad_requests)} 门课, 将并发抢课 (模拟同时打开 {len(grad_requests)} 个选课页面)...")
    for entry in entries:
        print(f"  - {entry[0]}")
    print(f"抢课间隔时间： {interval} 秒...")

    threads = []
    for entry in entries:
        t = threading.Thread(target=grad_worker, args=(entry, success_set, lock, stop_event), daemon=True)
        threads.append(t)
    for t in threads:
        t.start()

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收到手动终止信号 (Ctrl+C), 正在停止所有线程...")
        stop_event.set()
        for t in threads:
            t.join(timeout=5)

    print("\n+===================================================================================+")
    print(" 脚本结束, 抢课结果汇总:")
    for entry in entries:
        status = ("已选上" if len(entry) == 4 else "检测到成功记录（未按目标ID核验）") if entry[0] in success_set else "未成功"
        print(f"  - {entry[0]}: {status}")
    print("未成功的课程下次运行脚本时会继续尝试 (已选上的课系统会提示已选)。")


# ================================ 入口 ================================

def main():
    if "替换" in headers["X-Token"]:
        print("错误: X-Token 未填写，请检查脚本配置！")
        exit()

    print("+===================================================================================+")
    print("                     TJ-CourseFetch-Pro  同济大学抢课脚本")
    print("+===================================================================================+")
    print("请选择本次抢课的模式:")
    print("  [1] 本科课   一次可保存多门课, 共用一对凭证, 需填写 teachClassId 列表")
    print("  [2] 研究生课 一次只能保存一门课, 每门课一对凭证, 并发模拟多个页面分别抢")
    choice = input("请输入 1 或 2 并回车: ").strip()

    if choice == "1":
        run_undergraduate()
    elif choice == "2":
        if not grad_requests:
            print("错误: 研究生模式的目标课程凭证列表 (grad_requests) 为空，请按照说明填写！")
            exit()
        for entry in grad_requests:
            if len(entry) < 3 or "替换" in entry[1] or "替换" in entry[2]:
                print(f"错误: grad_requests 中 '{entry[0] if entry else '?'} 的 ciphertext/checkCode 未填写完整，请检查脚本配置！")
                exit()
        run_graduate()
    else:
        print("无效的输入，请重新运行脚本并输入 1 或 2。")
        exit()


if __name__ == "__main__":
    main()
