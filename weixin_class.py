#-*- coding:utf-8 -*-
import urllib
import urllib2
import cookielib
import json
import re
import md5
from urllib import quote
from urllib import unquote

#------------微信公告平台账号密码-------------
username='xxx'
pwd='xxx'
pwd=md5.md5(pwd)
pwd=pwd.hexdigest()

class Weixin(object):
        def __init__(self):
                self.token=''
                self.fakeid=''
#-----------模拟登陆，并返回token---------------
        def login(self):
                cj=cookielib.LWPCookieJar()
                opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                urllib2.install_opener(opener)
                """ 以上是cookie部分，貌似没用"""
                paras={'username':username,'pwd':pwd,'imgcode':'','f':'json'}
                req=urllib2.Request('https://mp.weixin.qq.com/cgi-bin/login?lang=zh_CN',urllib.urlencode(paras))
                req.add_header('Accept','application/json, text/javascript, */*; q=0.01')
                req.add_header('Accept-Encoding','gzip,deflate,sdch')
                req.add_header('Accept-Language','zh-CN,zh;q=0.8')
                req.add_header('Connection','keep-alive')
                req.add_header('Content-Length','79')
                req.add_header('Content-Type','application/x-www-form-urlencoded; charset=UTF-8')
                req.add_header('Host','mp.weixin.qq.com')
                req.add_header('Origin','https://mp.weixin.qq.com')
                req.add_header('Referer','https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN')
                req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.76 Safari/537.36')
                req.add_header('X-Requested-With','XMLHttpRequest')
                ret=urllib2.urlopen(req)
                real_url=ret.geturl()
                retread=ret.read()
                print retread
                token=json.loads(retread)
                token= re.search(r'token=(\d+)',token['redirect_url'])
                self.token=token.group(1)
                print self.token
                
                
#-----------获得信息列表---------------
        def get_msglist(self):
                url='https://mp.weixin.qq.com/cgi-bin/message?t=message/list&token=%s&count=20&day=7'%self.token
                req=urllib2.Request(url)
                req.add_header('x-requested-with','XMLHttpRequest')
                req.add_header('referer','https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN')
                ret=urllib2.urlopen(req)
                html=ret.read()
                f=open('tmp.txt','w+')
                f.write(html)
                f.close()
                c = "".join(html.split())
                msglist =  re.findall(r'"nick_name":"(.*?)"',c)
                for i in range(len(msglist)):
                        msglist[i]=quote(msglist[i])
                result=unquote(json.dumps(msglist))
                f=open('person.json','w')
                f.write(result)
                f.close()
                

#-----------获得图片---------------
        def get_img(self):
                self.fakeid='1383525141'
                url = "https://mp.weixin.qq.com/misc/getheadimg?token=%s&fakeid=%s"%(self.token,self.fakeid)
                req=urllib2.Request(url)
                rst=urllib2.urlopen(req)
                if rst:
                        f=open(r'%s.jpg'%self.fakeid,'wb+')
                        f.write(rst.read())
                        f.close()
                        return 'true'
                else:
                        return 'false'
if __name__=='__main__':
        weixin=Weixin()
        weixin.login()
        weixin.get_msglist()
        weixin.get_img()
