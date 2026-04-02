# -*- coding: utf8 -*-
import os
from hashlib import md5

from requests import post, session
from requests.exceptions import RequestException

try:
    import pretty_errors  # noqa: F401
except ImportError:
    pretty_errors = None


TBS_URL = "http://tieba.baidu.com/dc/common/tbs"
LIKES_URL = "https://tieba.baidu.com/mo/q/newmoindex?"
SIGN_URL = "http://c.tieba.baidu.com/c/c/forum/sign"


class Tieba:
    def __init__(self, bduss, stoken):
        self.BDUSS = bduss
        self.STOKEN = stoken
        self.success_list = []
        self.result = {}
        self.sign_list = []
        self.fail_list = []
        self.rest = set()
        self.already = set()
        self.tbs = ""
        self.session = session()
        self.session.headers.update(
            {
                "Accept": "text/html, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Host": "tieba.baidu.com",
                "Referer": "http://tieba.baidu.com/i/i/forum",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

    def set_cookie(self):
        self.session.cookies.update({"BDUSS": self.BDUSS, "STOKEN": self.STOKEN})

    def fetch_tbs(self):
        response = self.session.get(TBS_URL).json()
        if response["is_login"] == 1:
            self.tbs = response["tbs"]
        else:
            raise Exception("获取tbs错误！以下为返回数据：" + str(response))

    def fetch_likes(self):
        self.rest.clear()
        self.already.clear()
        response = self.session.get(LIKES_URL).json()
        if response["no"] != 0:
            raise Exception("获取关注贴吧错误！以下为返回数据：" + str(response))
        for forum in response["data"]["like_forum"]:
            if forum["is_sign"] == 1:
                self.already.add(forum["forum_name"])
            else:
                self.rest.add(forum["forum_name"])

    def sign(self, forum_name):
        data = {
            "kw": forum_name,
            "tbs": self.tbs,
            "sign": md5(f"kw={forum_name}tbs={self.tbs}tiebaclient!!!".encode("utf8")).hexdigest(),
        }
        response = self.session.post(SIGN_URL, data).json()
        error_code = response["error_code"]
        if error_code == "160002":
            print(f'"{forum_name}"已签到')
            self.sign_list.append(forum_name)
            return True
        if error_code == "0":
            rank = response["user_info"]["user_sign_rank"]
            print(f'"{forum_name}">>>>>>>签到成功，您是第{rank}个签到的用户！')
            self.result[forum_name] = response
            self.success_list.append(forum_name)
            return True
        print(f'"{forum_name}"签到失败！以下为返回数据：{str(response)}')
        self.fail_list.append(forum_name)
        return False

    def loop(self, n):
        print(f"* 开始第{n}轮签到 *")
        rest = set()
        self.fetch_tbs()
        for forum_name in self.rest:
            if not self.sign(forum_name):
                rest.add(forum_name)
        self.rest = rest

    def run(self, max_retry):
        self.set_cookie()
        self.fetch_likes()
        if self.already:
            print("---------- 已经签到的贴吧 ---------")
            for forum_name in self.already:
                print(f'"{forum_name}"已签到')
                self.sign_list.append(forum_name)
        round_index = 0
        while round_index < max_retry and self.rest:
            round_index += 1
            self.loop(round_index)
        if self.rest:
            print("--------- 签到失败列表 ----------")
            for forum_name in self.rest:
                print(f'"{forum_name}"签到失败！')

    def build_report(self):
        success_lines = ["", "- **签到成功贴吧**：", ""]
        for forum in self.success_list:
            sign_rank = self.result[forum]["user_info"]["user_sign_rank"]
            success_lines.append(f"    {forum}（签到成功，第{sign_rank}个签到）")

        fail_lines = ["", "- **签到失败贴吧**：", ""]
        fail_lines.extend([f"    {forum}" for forum in self.fail_list])

        signed_lines = ["", "- **已经签到的贴吧**：", ""]
        signed_lines.extend([f"    {forum}" for forum in self.sign_list])

        summary = (
            f"共关注了{len(self.already) + len(self.rest)}个贴吧，本次成功签到了{len(self.success_list)}个，"
            f"失败了{len(self.fail_list)}个，有{len(self.sign_list)}个贴吧已经签到。"
        )
        return "\n".join([summary] + success_lines + fail_lines + signed_lines)


def parse_bduss_accounts(raw_value):
    if not raw_value:
        return []
    normalized = raw_value.replace("\n", ",").replace("&", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def send_wechat(serverchan_sckey, msg):
    resp = post(f"https://sc.ftqq.com/{serverchan_sckey}.send", params={"text": "贴吧签到结果", "desp": msg})
    if resp.status_code == 200:
        print("微信推送成功")
    else:
        print("微信推送失败")


if __name__ == "__main__":
    bduss_accounts = parse_bduss_accounts(os.getenv("TIEBA_BDUSS", ""))
    if not bduss_accounts:
        bduss_accounts = ["****此处替换为百度账号BDUSS****"]
    stoken = os.getenv("TIEBA_STOKEN", "")
    sckey = os.getenv("SERVERCHAN_SCKEY", "****此处替换为Server酱SCKEY****")
    max_retry = int(os.getenv("TIEBA_MAX_RETRY", "3"))

    reports = []
    for index, bduss in enumerate(bduss_accounts, start=1):
        print(f"\n======================== 账号{index} ========================\n")
        try:
            task = Tieba(bduss, stoken)
            task.run(max_retry)
            reports.append(task.build_report())
        except RequestException as exc:
            error_report = f"账号{index}签到异常：网络请求失败，错误信息：{exc}"
            print(error_report)
            reports.append(error_report)
        except Exception as exc:
            error_report = f"账号{index}签到异常：{exc}"
            print(error_report)
            reports.append(error_report)

    final_report = "\n\n".join(reports)
    if sckey and "****此处替换为Server酱SCKEY****" not in sckey:
        send_wechat(sckey, final_report)

    print("--------- 本日签到报告 -----------")
    print(final_report)
