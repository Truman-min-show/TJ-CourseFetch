from pprint import pprint

import requests
import time

# 请在第一次选课保存课表时使用F12抓包获取以下信息：
# 此处放置X-Token(校验选课用户)
headers = \
{
    "X-Token": "f8a10876cdf94c8280664afb09065ef8",
}
# 此处放置ciphertext和checkCode(校验选课信息和选课信息有效性)
data = \
    {"ciphertext":"bsLH%2BdHOPnskqeT8qk0nGs%2BKa%2BSUD04DlD7K1IQrvwws9Wf5iI2T7NGRL9dBhmd0VLotDmsPYOiW%2B6iP6Zs8G2Zns7GQ1UbP7eLP3dOLIDPU9CPGLbNkhchYA4YNrjfrA2K5qEFRuUybjZcmJHgsms7boVTco%2BJh%2B9djs4nHHMKqnnM9YxWKH0omtLWjR7KMkFAgkDzwxPwMTwozXnJxUChUt6IZG%2FuSkp4Xz29HMdRCnhBOiawVGxeR9XG2rTKuRrxQK5OPK6aB5BxHgnl3SFYAXY5AQu2YMcFnWJrtISq8yAXT1Zbozp%2FZD3UDG63wkizghYSTtko2GCNDR0wT27upQdU3BGS0ic13brCVhblzTPNlGQVF7GUnhElZzA9lzmrc9CZUkpqiXnuNbMlW8lAEkLj9uYA35aIlgX%2BDbFv3Y3sTe%2FXeRrAnopQaFNyLf6%2Fj%2BmVsZXZ8AQHS01hbaEHd2xRraBjg%2FdApTQ%2FZEcQ8zQLYGk1K8%2Btz7XrHvMduCEx%2B3nas1Vuv5tCpd5QkyGy3BAmLDiuJ1xATyiRk%2FV%2BPOduOkOhjreW%2F5%2BIS64ZMTSksdXaQQTJwwx1jgB5WQn9vR0H77k6TTEoJJVgV8t5wTObuGKEOJaf3mxGWXpSHQ662Dl%2BE5aOzEJ6xCqUqW3UvpSRtHQ8ej1XlACl3msjXvNHQzkr24GNkVIT1Enif0IbZn4SJ2vRmnHDh%2FycovN6zZsKnRSFMpg8ZXbW595xXhI2PiL5j1Gys8K8QrZcamk8bF4%2BRVJD2oimsi9dssq8qsDMe06Dq0PN0Fp55T0JgNXa8NvsJa3fsDscRt9dSOEbbYym52HLK2OnYRrJP62GsvGCMLvO17yLvynGudkKyNZVJZx0pU3GQ5N4ymr8Hz%2FfPW0%2BrKB0wd1%2F3GTDY5tBgSkMCWXs8dqs8QUp1AJbck2Xoj0g0TYQGklC78hrBiC7o%2Bi%2BD65aQNWJk7uP1tVkYjJ1VoNnO%2F%2BL3TI0ZFaz0zD5rj0JoLmPgyA6a3zNhHqryZdLtwagHxDPlpNQ7hr665%2BfmuKYLglI5o9x8WPIu%2BuMV2hm0ySYlF8%2Fa0lXqC9jYRWRn5wDq4cKLYvAtlB%2Bcl%2BBv2GCWdPngeU2iGjoWK%2BIFamSbBdGeKUnZbed8CrdpiY4hgmuTvZ73670jFTkLSf704J%2FUruSCy1WOQsOkjwZr9GhuEfyVjkgufBJOnMdIffqCNxkZJHJ1u007zWzJRlsv9b13OnBoAKwQSVo6bXCKI34ij5wtrsVWGF54qFb6W6YHSTEygMXqYt55YGAGe9JnmfMciNJT6R1K%2FLENOkh5f7rDKHPE27SUvTKDq7XOB%2BUFGOtj36C7sjWKRU%2FnrPnDsnXqPUt2XFTZWIcNyVQpdDrjR9Bil68N9lWwFUkWxnzJzBM3lZotCHJVp5iBzlAYKiUgwlgb9V1i69ZNFRVprWUc9MbvZa0%2FYtTlGqWA2yBJZkfcjBWZ%2Fdu3jrf%2BZWSN1QcWpU%2FMjJjCr9AH6HtMyAEd5LyVoPVsPkaT","checkCode":"4d2f34463d18af20fb50c0b533561eac"
     }

rqstUrl = "https://1.tongji.edu.cn/api/electionservice/student/elect"
statusUrl = "https://1.tongji.edu.cn/api/electionservice/student/5435/electRes"
response1 = requests.post(rqstUrl, json=data, headers=headers)

print("正在核验Token和选课信息有效性...")
if response1.text == '{"message":"sessionid is not exist."}':
    print("选课会话不存在, 请检查输入是否正确或过期...")
    exit()
else:
    print("选课信息有效, 开始自动选课...")

tryCount = 0
successList = []
interval = 3

# 现在还有点问题没改，选课成功会报错，失败不会，所以一直挂着到报错就表示选上了。选课系统关闭之后还能继续用，只要Token没过期。
while True:
    tryCount += 1
    print("\n+===================================================================================+\n")
    print("第" + str(tryCount) + "次尝试: ", end="")
    response1 = requests.post(rqstUrl, json=data, headers=headers)
    if response1.text == '{"message":"sessionid is not exist."}':
        print("选课会话不存在, 请检查输入是否正确或过期...")
        exit()
    data1 = response1.json()
    print("已请求, 等待查询结果...")
    time.sleep(interval)
    response2 = requests.post(statusUrl, headers=headers)
    data2 = response2.json()
    if (not response2.text) or (data2["data"]["successCourses"].__len__()
                                + data2["data"]["failedReasons"].__len__() == 0):
        print("此次尝试未收到响应...")
    if response2.text and data2["data"]["successCourses"].__len__() > 0:
        print("有课程选课成功! 选课成功的课程: ")
        pprint(data2["data"]["successCourses"])
        for course in data2["data"]["successCourses"]:
            if int(course["courseId"]) not in successList:
                successList.append(int(course["courseId"]))
    if response2.text and data2["data"]["failedReasons"].__len__() > 0:
        print("有课程选课失败! 失败原因汇总如下: ")
        print(str(data2["data"]["failedReasons"]).replace("{", "").replace("}", "").replace(", ", "\n"))
    print("已尝试" + str(tryCount) + "次: ")
    if successList.__len__() == 0:
        print("暂无成功课程...")
    else:
        print("恭喜您，有以下成功选课的课程: ")
        pprint(successList)