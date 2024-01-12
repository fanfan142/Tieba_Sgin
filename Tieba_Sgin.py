# -*- coding: utf8 -*-
from requests import session, post
from hashlib import md5
from random import random
from time import sleep
import pretty_errors

class Tieba():
    def __init__(self, BDUSS, STOKEN):
        self.BDUSS = '****此处替换为百度账号的BDUSS****'
        self.STOKEN = STOKEN
        self.success_list = []
        self.sign_list = []
        self.fail_list = []
        self.session = session()
        self.session.headers.update(
            {'Accept': 'text/html, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'tieba.baidu.com',
            'Referer': 'http://tieba.baidu.com/i/i/forum',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/71.0.3578.98 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'}
        )
    def set_cookie(self):
        self.session.cookies.update({'BDUSS': self.BDUSS, 'STOKEN': self.STOKEN})
    def fetch_tbs(self):
        r = self.session.get('http://tieba.baidu.com/dc/common/tbs').json()
        if r['is_login'] == 1: self.tbs = r['tbs']
        else: raise Exception('获取tbs错误！以下为返回数据：' + str(r))
    def fetch_likes(self):
        self.rest = set()
        self.already = set()
        r = self.session.get('https://tieba.baidu.com/mo/q/newmoindex?').json()
        if r['no'] == 0:
            for forum in r['data']['like_forum']:
                if forum['is_sign'] == 1:
                    self.already.add(forum['forum_name'])
                else:
                    self.rest.add(forum['forum_name'])
        else: raise Exception('获取关注贴吧错误！以下为返回数据：' + str(r))
    def sign(self, forum_name):
        data = {
            'kw': forum_name,
            'tbs': self.tbs,
            'sign': md5(f'kw={forum_name}tbs={self.tbs}tiebaclient!!!'.encode('utf8')).hexdigest()
        }
        r = self.session.post('http://c.tieba.baidu.com/c/c/forum/sign', data).json()
        if r['error_code'] == '160002':
            print(f'"{forum_name}"已签到')
            self.sign_list.append(forum_name)
            return True
        elif r['error_code'] == '0':
            print(f'"{forum_name}">>>>>>>签到成功，您是第{r["user_info"]["user_sign_rank"]}个签到的用户！') # Modify!
            self.success_list.append(forum_name)
            return True
        else:
            print(f'"{forum_name}"签到失败！以下为返回数据：{str(r)}')
            self.fail_list.append(forum_name)
            return False
    # 对签到失败的贴吧进行重试
    def loop(self, n):
        print(f'* 开始第{n}轮签到 *')
        rest = set()
        self.fetch_tbs()
        for forum_name in self.rest:
            flag = self.sign(forum_name)
            if not flag: rest.add(forum_name)
        self.rest = rest

        if n >= 10:  # 最大重试次数
            self.rest = set()

    def main(self, max):
        self.set_cookie()
        self.fetch_likes()
        n = 0
        if self.already:
            print('---------- 已经签到的贴吧 ---------')
            for forum_name in self.already:
                print(f'"{forum_name}"已签到')
                self.sign_list.append(forum_name)
        while n < max and self.rest:
            n += 1
            self.loop(n)

        if self.rest:
            print('--------- 签到失败列表 ----------')
            for forum_name in self.rest:
                print(f'"{forum_name}"签到失败！')

#def main_handler(*args):
    #with open('BDUSS.txt') as f: BDUSS = f.read()
    #with open('STOKEN.txt') as f: STOKEN = f.read()

def send_wechat(msg):
    resp = post(f'https://sc.ftqq.com/{sckey}.send', params={'text': '贴吧签到结果', 'desp': msg})
    if resp.status_code == 200:
        print('微信推送成功')
    else:
        print('微信推送失败')


if __name__ == "__main__":
    
    BDUSS=[""]
    
    STOKEN=''
    sckey = '****此处替换为Server酱SCKEY****'
    for param in BDUSS:
        # 多账号签到
        task = Tieba(param, STOKEN)
        print("\n========================\n")
        task.main(3)

    # 遍历签到成功的贴吧列表，每个贴吧名称单独一行，附带签到排名
    success_list = f'\n\n- **签到成功贴吧**：\n\n'
    for forum in task.success_list:
        sign_rank = task.result[forum]['user_info']['user_sign_rank']
        success_list += f'    {forum}  （签到成功，第{sign_rank}个签到）\n'
    
    # 遍历已经签到的贴吧列表，每个贴吧名称单独一行
    sign_list = f'\n\n- **已经签到成功的贴吧**：\n\n' + "\n\n".join([f'    {forum}' for forum in task.sign_list])

    # 遍历签到失败的贴吧列表，每个贴吧名称单独一行
    fail_list = f'\n\n- **签到失败贴吧**：\n\n' + "\n\n".join([f'    {forum}' for forum in task.fail_list])

    #消息推送内容
    msg = f'共关注了{len(task.already) + len(task.rest)}个贴吧，本次成功签到了{len(task.success_list)}个，失败了{len(task.fail_list)}个，有{len(task.sign_list)}个贴吧已经签到。' \
      f'{success_list}{fail_list}{sign_list}'
    if sckey:
        send_wechat(msg)
    print('--------- 本日签到报告 -----------')
    print(msg)
    if task.fail_list:
        print('--------- 签到失败列表 ----------')
        for forum_name in task.fail_list:
            print(f'"{forum_name}"签到失败！')
