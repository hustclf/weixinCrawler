# -*- coding:utf-8 -*-
import urllib
import urllib2
import cookielib
import json
import re
import md5
import time
import requests
import sys

class Weixin(object):

    def __init__(self, username, pwd):
        self.status = False
        self._username = username
        self._pwd = md5.md5(pwd)
        self._pwd = self._pwd.hexdigest()
        self._token = ''
        self._ticketid = ''
        self._ticket = ''
        self._home_url = ''
        self._fileid = ''
        
        self.cj = cookielib.LWPCookieJar()
        self.status = self._login()

    def _load_ticket(self):
        url = self._home_url
        req = urllib2.Request(url)
        req.add_header("Host", 'mp.weixin.qq.com')
        req.add_header('referer', 'https://mp.weixin.qq.com/')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/29.0.1547.76 Safari/537.36')
        ret = urllib2.urlopen(req)
        html = ret.read()
        self._ticket = re.search(r'ticket:[\"](.+?)[\"]', html).group(1)
        self._ticketid = re.search(r'user_name:[\"](.+?)[\"]', html).group(1)
        print("ticket id:" + self._ticketid)
        print("ticket:" + self._ticket)

    # -----------模拟登陆，并返回token---------------
    def _login(self):
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)

        paras = {'username': self._username, 'pwd': self._pwd, 'imgcode':'', 'f':'json'}
        req = urllib2.Request('https://mp.weixin.qq.com/cgi-bin/login?lang=zh_CN', urllib.urlencode(paras))
        req.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
        req.add_header('Accept-Encoding', 'gzip,deflate,sdch')
        req.add_header('Accept-Language', 'zh-CN,zh;q=0.8')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Content-Length', '79')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        req.add_header('Host', 'mp.weixin.qq.com')
        req.add_header('Origin', 'https://mp.weixin.qq.com')
        req.add_header('Referer', 'https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/29.0.1547.76 Safari/537.36')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        ret = urllib2.urlopen(req)
        retread = ret.read()
        token = json.loads(retread)
        self._home_url = "https://mp.weixin.qq.com/" + token['redirect_url']
        token = re.search(r'token=(\d+)', token['redirect_url'])
        if not token:
            return False
        else:
            self._token = token.group(1)
            print self._token
            self._load_ticket()
            return True

    # --------上传关注事件回复（图片）---------------------
    """
    当用户关注公众账号时，返回一张图片
    该函数用于该图片的上传
    """
    def upload_img(self, file_name):
        url = 'https://mp.weixin.qq.com/cgi-bin/filetransfer?action=upload_material&f=json&scene=5' \
              '&writetype=doublewrite&groupid=1&ticket_id={ticket_id}' \
              '&ticket={ticket}&svr_time={timestamp}&token={token}&lang=zh_CN&seq=1'.format(
                ticket_id=self._ticketid,
                ticket=self._ticket,
                timestamp=int(time.time()),
                token=self._token,
                )
        try:
            files = {'file': open(file_name, 'rb')}
        except IOError:
            raise ValueError('file not exist')
        payloads = {
            'Filename': file_name,
            'folder': '/cgi-bin/uploads',
            'Upload': 'Submit Query',
        }

        r = requests.post(url, files=files, data=payloads, cookies=self.cj)

        message = json.loads(r.text)
        self._fileid = message['content']

    # -------上传自动回复的图片后，保存设置使之生效----------
    def confirm_img(self):
    """
    当用户关注公众账号时，返回一张图片
    该函数用于上传图片成功后，保存设置使之生效
    """
        url = "https://mp.weixin.qq.com/advanced/setreplyrule?cgi=setreplyrule&fun=save&t=ajax-response" \
              "&token={token}&lang=zh_CN".format(
                token=self._token
                )
        payload = {
            'token': self._token,
            'lang': "zh_CN",
            'f': "json",
            "ajax": 1,
            "random": 0.16296246835532013,
            "type": 2,
            "fileid": self._fileid,
            "replytype": "beadded"
        }
        headers = {
            "referer": "https://mp.weixin.qq.com/advanced/autoreply?t=ivr/reply&action=beadded"
                       "&token={token}&lang=zh_CN".format(token=self._token)
        }
        r = requests.post(url, data=payload, headers=headers, cookies=self.cj)
        message = json.loads(r.text)
        print(message)

    # --------上传微信公众账号的头像---------------------
    def upload_preview_img(self, file_name):
        url = 'https://mp.weixin.qq.com/cgi-bin/filetransfer?action=preview&f=json' \
              '&ticket_id={ticket}&ticket={ticket}&svr_time={timestamp}&' \
              'token={token}&lang=zh_CN&seq=2'.format(
                ticket_id=self._ticketid,
                ticket=self._ticket,
                timestamp=int(time.time()),
                token=self._token,
                )
        try:
            files = {'file': open(file_name, 'rb')}
        except IOError:
            raise ValueError('file not exist')

        headers = {
            "referer": "https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index&token={token}&lang=zh_CN".format(
                token=self._token)
        }
        r = requests.post(url, files=files,  headers=headers, cookies=self.cj)

        message = json.loads(r.text)
        print(message)
        self._fileid = message['content']

    # -------上传微信公众账号头像后，保存设置，使之生效----------
    def confirm_preview_img(self):
        url = "https://mp.weixin.qq.com/misc/cropimg?t=ajax-response&token={token}&lang=zh_CN".format(
                token=self._token
                )

        payload = {
            'token': self._token,
            'lang': "zh_CN",
            'f': "json",
            "ajax": 1,
            "random": 0.66296246835532013,
            "fid": self._fileid,
            "x1": 0,
            "y1": 0,
            "x2": 1,
            "y2": 1,
            "width": 120,
            "height": 120,
            "x": 0,
            "y": 0
        }

        headers = {
            "referer": "https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index&token={token}&lang=zh_CN"
                       .format(token=self._token),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/29.0.1547.76 Safari/537.36',
            'Host': 'mp.weixin.qq.com',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://mp.weixin.qq.com',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Pragma': "no-cache",
            "Accept-Encoding": "gzip, deflate"
        }
        r = requests.post(url, data=payload, headers=headers, cookies=self.cj)
        message = json.loads(r.text)
        print(message)

    # -----检测要微信公众号是否合法-----------
    def is_weixin_nick_name_valid(self, nick_name):
        """
        该函数用来检测要设置的微信公众号名称是否合法，非法情况有 1 需要审核（错误码：4） 2 禁止设置（错误码：1） 3 微信公众号已经存在（错误码：62004）
        """
        url = "https://mp.weixin.qq.com/cgi-bin/setuserinfo?action=check_nickname"
        headers = {
            'referer': "https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index&token={token}"
                       "&lang=zh_CN".format(token=self._token)
        }
        payload = {
            'token': self._token,
            'lang': "zh_CN",
            'f': "json",
            'ajax': '1',
            'random': 0.7410682854330337,
            'nick_name': nick_name,
        }
        r = requests.post(url, data=payload, headers=headers, cookies=self.cj)
        message = json.loads(r.text)

        if message['base_resp']['ret'] == 4:
            print("This nick_name need check by weixin group")
        elif message['base_resp']['ret'] == 1:
            print("This nick_name can not be set")
        elif message['base_resp']['ret'] == 62004:
            print("this nick_name has exist,please choose another one")
        else:
            print("This nick_name is valid")
        return message['base_resp']['ret']
        
    # --------设置微信公众号-------------
    """
    该函数用来设置微信公众号
    调用前，必须使用is_weixin_nick_name_valid确保传过来的nick_name是合法的nick_name
    """
    def set_weixin_nick_name(self, nick_name):
        url = "https://mp.weixin.qq.com/cgi-bin/setuserinfo?action=nickname"
        headers = {
            'referer': "https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index"
                       "&token={token}&lang=zh_CN".format(token=self._token)
        }
        payload = {
            'token': self._token,
            'lang': "zh_CN",
            'f': "json",
            'ajax': '1',
            'random': 0.7410682854330337,
            'nick_name': nick_name,
            'invade_type': 0
        }
        r = requests.post(url, data=payload, headers=headers, cookies=self.cj)
        message = json.loads(r.text)
        if message['base_resp']['ret'] == 200002:
            print("Weixin name has been set before, you are not allowed to set again")
        else:
            print("Weixin name has been set")
        return message['base_resp']['ret']

    # -----修改微信号介绍------------------
    def change_weixin_info(self, intro):
        url = "https://mp.weixin.qq.com/cgi-bin/setuserinfo?action=intro&t=ajax-response" \
              "&token={token}&lang=zh_CN".format(
                token=self._token
                )
        headers = {
            'referer': "https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index&token={token}&lang=zh_CN".format(token=self.token),
        }
        payload = {
            'token': self._token,
            'lang': "zh_CN",
            'f': "json",
            'random': 0.7410682854330337,
            'intro': intro,
        }
        r = requests.post(url, data=payload, headers=headers, cookies=self.cj)
        message = json.loads(r.text)
        print(message)
    
if __name__ == '__main__':

    weixin = Weixin("xxxxx", "xxxxx")
    if weixin.status == False:
        print("Login failed")
        sys.exit(-1)
        
    # ----修改自动回复的图片------
    # weixin.upload_img("some file")
    # weixin.confirm_img()
    
    # ----修改微信公众号头像------
    # weixin.upload_preview_img(touxiang_imgs[count_touxiang])
    # weixin.confirm_preview_img()

    # ---修改微信公众号介绍------
    #weixin.change_weixin_info(intros[count_intro])
    
    # ---修改微信名称--------
    nick_name = "hustclf"
    result = weixin.is_weixin_nick_name_valid(nick_name)
    if result:
        weixin.set_weixin_nick_name(nick_name)
    else:
        print("weixin nick_name is invalid")
