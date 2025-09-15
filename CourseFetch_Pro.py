import requests
import time
from pprint import pprint
import json

# ================================ 用户配置指南 (必读) ================================
#
# 您需要通过浏览器的F12开发者工具来获取以下所有信息。
#
# --- Part 1: 获取身份与选课凭证 ---
#   1. 登录选课系统，打开F12开发者工具，切换到 "Network" (网络) 选项卡。
#   2. 在页面上进行一次“保存课表”的操作。
#   3. 在F12的网络请求列表中，找到一个名为 "elect" 的请求，点击它。
#
#   - ToDo 1: 获取 X-Token
#     在 "elect" 请求的 "Headers" (请求头) 部分，找到 "X-Token" 字段，复制其值。
#
#   - ToDo 2: 获取 ciphertext 和 checkCode
#     在 "elect" 请求的 "Payload" (载荷) 或 "Request" (请求) 部分，找到并复制 "ciphertext" 和 "checkCode" 的值。
#
# --- Part 2: 获取课程的内部ID (teachClassId) ---
#   1. 仍在F12的 "Network" 选项卡。
#   2. 将选课的“结果”关闭（注意要点击弹窗的下面的关闭按钮而不是直接点右上角的“×”）。
#   3. 在网络请求列表中，找到一个返回了大量课程信息的JSON文件。
#      (这个请求的名字可能是以getTeachClass4Limit?为开头的一长串url请求)
#   4. 点击这个请求，查看其 "Response" (响应) 或 "Preview" (预览)。
#
#   - ToDo 3: 获取 teachClassId
#     在搜索到的课程信息中，找到 "teachClassId" 字段，复制其值 (是一长串以1111...开头的数字)。
#     为您想抢的每一门课都重复此操作。（注意同一门课的不同时间段有不同的teachClassId,请对照您要抢的时间段的课程序号与teachClassCode字段的值是否对应）
#
# ================================ 用户配置区域 (请将抓取的值填入下方) ================================

# ToDo 1: 填入您的 X-Token
headers = {
    "X-Token": "在这里替换成你自己的X-Token",
}

# ToDo 2: 填入您的 ciphertext 和 checkCode
data = {
    "ciphertext": "在这里替换成你自己的ciphertext",
    "checkCode": "在这里替换成你自己的checkCode"
}

# ToDo 3: 填入您想抢的所有课程的【teachClassId】列表
# 例如: targetCourseIds = [1111111124934476, 1111111124934261] #这是嵌入式系统和机器学习的
targetCourseIds = []

# (可选) 请求间隔, 单位秒
interval = 3

# ================================ 脚本主逻辑区 (无需修改) ================================

# (后续代码与之前稳定版相同)
rqstUrl = "https://1.tongji.edu.cn/api/electionservice/student/elect"
statusUrl = "https://1.tongji.edu.cn/api/electionservice/student/5435/electRes"

# 检查配置是否完整
if "替换" in headers["X-Token"] or "替换" in data["ciphertext"] or "替换" in data["checkCode"]:
    print("错误: X-Token, ciphertext, 或 checkCode 未填写，请检查脚本配置！")
    exit()
if not targetCourseIds:
    print("错误: 目标课程ID列表 (targetCourseIds) 为空，请按照说明填写课程的【teachClassId】！")
    exit()

print("正在核验Token和选课信息有效性...")
try:
    response1 = requests.post(rqstUrl, json=data, headers=headers)
    if response1.text == '{"message":"sessionid is not exist."}':
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
        requests.post(rqstUrl, json=data, headers=headers)
        print("已发送选课请求, 等待查询选课结果...")
        time.sleep(interval)

        response_status = requests.post(statusUrl, headers=headers)
        status_data = response_status.json()

        if status_data and "data" in status_data and "successCourses" in status_data["data"]:
            returned_ids = status_data["data"]["successCourses"]
            if returned_ids:
                print(" 有课程选课成功! 返回的 teachClassId 如下: ")
                pprint(returned_ids)
                for course_id in returned_ids:
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