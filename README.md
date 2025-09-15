

### 使用步骤：

1.  **准备工作：安装 Python 和 requests 库**

      * 确保你的电脑上安装了 Python。
      * 打开终端（命令行），安装 `requests` 库，如果尚未安装的话，可以使用以下命令：
        ```bash
        pip install requests
        ```

2.  **获取个人选课信息（最关键的一步）**

      * 登录学校的选课系统。
      * 在选课页面，按下 `F12` 键打开浏览器的开发者工具，然后切换到 “Network” (网络) 选项卡。
      * 手动进行一次选课操作，比如勾选一门课程后点击“保存课表”。
      * 在开发者工具的请求列表中，找到一个名为 `elect` 的请求。点击这个请求，查看其详细信息。
      * **获取 `X-Token`**: 在 `elect` 请求的 “Headers” (请求头) 部分，找到 `X-Token` 字段，并复制它的值。
      * **获取 `ciphertext` 和 `checkCode`**: 同样在 `elect` 请求中，切换到 “Payload” (有效载荷) 或 “Request” (请求) 部分，你会看到 `ciphertext` 和 `checkCode` 字段，复制它们的值。

3.  **配置脚本文件 `CourseFetch.py`**

      * 用文本编辑器（如 VS Code, Sublime Text, 记事本等）打开 `CourseFetch.py` 文件。
      * 将你刚刚复制的 `X-Token` 字符串粘贴到 `headers` 变量的引号内，替换掉原来的示例值。
        ```python
        headers = \
        {
            "X-Token": "这里替换成你自己的X-Token",
        }
        ```
      * 将你复制的 `ciphertext` 和 `checkCode` 字符串粘贴到 `data` 变量中对应的位置，替换掉原来的示例值。
        ```python
        data = \
            {"ciphertext":"这里替换成你自己的ciphertext",
             "checkCode":"这里替换成你自己的checkCode"
             }
        ```

4.  **（可选）调整请求间隔 `interval`**

      * 根据你同学的建议，你可以修改脚本中的 `interval` 变量的值。这个值代表每次尝试抢课之间的时间间隔，单位是秒。默认是 `3` 秒。如果想提高抢课频率，可以适当调小这个数值，但不要太小，以免给服务器造成太大压力或被封禁。
        ```python
        interval = 3 # 可以修改这个数字，例如 interval = 1.5
        ```

5.  **运行脚本**

      * 打开终端（命令行），进入 `CourseFetch.py` 文件所在的文件夹。
      * 运行以下命令来启动脚本：
        ```bash
        python CourseFetch.py
        ```
      * 脚本会首先验证你的 `Token` 和选课信息是否有效。如果有效，它会开始循环尝试抢课，并显示每一次的尝试结果。

### 注意事项：

  * **脚本的报错逻辑**: 根据代码注释，这个脚本有一个特点：“选课成功会报错，失败不会，所以一直挂着到报错就表示选上了”。所以当你看到脚本因为报错而停止运行时，很可能意味着你已经抢到课了。
  * **Token 的时效性**: `X-Token` 是有有效期的。如果脚本提示 "sessionid is not exist." 或 "选课会话不存在"，说明你的 Token 过期了，需要重复第二步，重新抓取最新的 `X-Token`, `ciphertext`, `checkCode` 来更新脚本。
  * **合法合规使用**: `README.md` 文件中特别强调，此脚本仅为方便选课，不得用于牟利或非法行为。

总结一下，核心就是通过浏览器抓包获取你自己的身份认证信息和选课请求信息，然后填入脚本中运行。
