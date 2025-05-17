#!/usr/bin/env python
# --coding:utf-8--
from futu import *
import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib import request, parse
import pymysql
from urllib.parse import quote
import datetime
import json

APP_ID = "cli_a5f7c86ba438100d"
APP_SECRET = "e9gotmZvQZl3Fk4nChNthdQBonAMyGRC"
APP_VERIFICATION_TOKEN = "ly8bErwCO7YxSYQ1gqxVzeW6rfzkJ2Wr"

# 实例化行情上下文对象
SysConfig.set_proto_fmt(ProtoFMT.Json)
quote_ctx = OpenQuoteContext(host="127.0.0.1", port=11111)

# 上下文控制
quote_ctx.start()              # 开启异步数据接收
quote_ctx.set_handler(TickerHandlerBase())  # 设置用于异步处理数据的回调对象(可派生支持自定义)
def GetOption(db):
    cursor = db.cursor()
    access_token = RequestHandler.get_tenant_access_token(None)
    chatidlist = RequestHandler.getChatGroupList(None, access_token)
    cursor.execute('select value from config where config_key="option_config"')
    resultset = cursor.fetchall()
    if len(resultset) == 0:
        return ""
    configlist = json.loads(resultset[0][0])
    text = ""
    for config_map in configlist:
        start_date = (datetime.date.today()+datetime.timedelta(days=30*int(config_map.get('option_timerange')))).strftime('%Y-%m-%d')
        print('start_date='+start_date)
        fin = open('/home/jiangqiquan/jqq/autotrader/Cron/options_filter_stock.txt', 'r')
        stock_list = []
        for line in fin.readlines():
            stock_list.append(line.strip()) 
        text = text + "\n今日满足要求期权：\n"
        options_list = []
        for code in stock_list:
            print('code:{}'.format(code))
            cursor.execute('select highest52weeks_price from snapshot where stockcode="'+code+'"')
            result = cursor.fetchall()
            if len(result) == 0:
                print('error code: {} do not have snapshot'.format(code))
                continue
            high_price = result[0][0]
            sql = "select option_code, stock_owner, strike_price,  strike_time from option where stock_owner='%s' and strike_time>='%s'" %(code, start_date)
            cursor.execute(sql)
            resultset = cursor.fetchall()
            for row in resultset:
                option_code = row[0]
                strike_price = row[2]
                print('code:{} strike_price:{} D:{}'.format(option_code, strike_price, high_price))
                if float(strike_price) >= 0.8 * float(high_price):
                    options_list.append(option_code)
        print('options_list:{}'.format(options_list))
        for i in range(int((len(options_list)-1)/400+1)):
            print('loop:{}'.format(i))
            ret1, data1 = quote_ctx.get_market_snapshot(options_list[400*i:400*i+400])
            if ret1 != RET_OK:
                print('get snapshot failed:{}'.format(data))
            else:
                print('snap:{}'.format(data1))
                for loopi in range(len(data1['code'])):
                    if data1['last_price'][loopi] <= float(config_map.get('option_price')) and data1['option_open_interest'][loopi] >= int(config_map.get('option_open_min')):
                        print('match code:{} price:{}'.format(data1['code'][loopi], data1['last_price'][loopi]))
                        line = "%s\t最新价:%.3f\t\n" % (data1['code'][loopi], data1['last_price'][loopi])
                        text = text + line
            time.sleep(1)
    return text

def isFloatNum(str):
    s = str.split('.')
    if len(s)>2:
        return False
    for si in s:
        if not si.isdigit():
            return False
    return True

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 解析请求 body
        req_body = self.rfile.read(int(self.headers['content-length']))
        obj = json.loads(req_body.decode("utf-8"))
        print(req_body)

        # 校验 verification token 是否匹配，token 不匹配说明该回调并非来自开发平台
        token = obj.get("token", "")
        if token != APP_VERIFICATION_TOKEN:
            print("verification token not match, token =", token)
            self.response("")
            return

        # 根据 type 处理不同类型事件
        type = obj.get("type", "")
        if "url_verification" == type:  # 验证请求 URL 是否有效
            self.handle_request_url_verify(obj)
        elif "event_callback" == type:  # 事件回调
            # 获取事件内容和类型，并进行相应处理，此处只关注给机器人推送的消息事件
            event = obj.get("event")
            if event.get("type", "") == "message":
                self.handle_message(event)
                return
        return

    def handle_request_url_verify(self, post_obj):
        # 原样返回 challenge 字段内容
        challenge = post_obj.get("challenge", "")
        rsp = {'challenge': challenge}
        self.response(json.dumps(rsp))
        return

    def handle_message(self, event):
        # 此处只处理 text 类型消息，其他类型消息忽略
        db = pymysql.connect(host="localhost", user="root", password="", db="futu", charset="utf8")
        cursor = db.cursor()

        msg_type = event.get("msg_type", "")
        event_type = event.get("type", "")
        chat_type = event.get("chat_type", "")
        if event_type != "message" or msg_type != "text":
            print("unknown msg_type =", msg_type)
            self.response("")
            db.close()
            return
        # 调用发消息 API 之前，先要获取 API 调用凭证：tenant_access_token
        access_token = self.get_tenant_access_token()
        if access_token == "":
            self.response("")
            db.close()
            return
        
        #获取技术指标
        print(event.get("text_without_at_bot", ""))
        msg = event.get("text_without_at_bot", "").strip()
        print('get_msg:{}'.format(msg))
        pos = msg.find(' ')
        if pos != -1:
            cmd = msg[0:pos]
            configstr = msg[pos+1:].strip()
        else:
            cmd = msg
            configstr = ''
        respmsg = ''
        print('cmd={}'.format(cmd))
        if cmd.upper() == 'CONFIG':
            if len(configstr) > 0:
                print('json:{}'.format(configstr))
                configlist = json.loads(configstr)
                valid = True
                for config in configlist:
                    open_min = config.get('option_open_min')
                    price = config.get('option_price')
                    timerange = config.get('option_timerange')
                    print('config:{} {} {}'.format(open_min, price, timerange))
                    if not open_min or not price or not timerange:
                        respmsg = '参数不合法'
                    else:
                        if timerange != int(timerange):
                            valid = False
                        if open_min != int(open_min):
                            valid = False
                        if not price>0:
                            valid = False
                        if not valid:
                            respmsg = '参数不合法'
                            break
                if valid:
                    cursor.execute("replace into config(config_key,value) values('option_config', '%s')" % (json.dumps(configlist)))
                    db.commit()
                    respmsg = '设置成功'
            else:
                cursor.execute('select value from config where config_key="option_config"')
                resultset = cursor.fetchall()
                for row in resultset:
                    respmsg = respmsg + '参数:' + row[0] + '\n'
                print('get config:{}'.format(respmsg))

        # 机器人 echo 收到的消息
        if respmsg:
            self.send_message(access_token, event.get("open_id"), "", respmsg)
            text = GetOption(db)
            print('get options return:{}'.format(text))
            self.send_message(access_token, event.get("open_id"), "", text)
            chatidlist = RequestHandler.getChatGroupList(None, access_token)
            for chatid in chatidlist:
                print(chatid)
                RequestHandler.send_message(None, access_token, "", chatid, respmsg)
                RequestHandler.send_message(None, access_token, "", chatid, text)

        self.response("")
        db.close()
        return

    def response(self, body):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body.encode())

    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type" : "application/json"
        }
        req_body = {
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return ""

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("get tenant_access_token error, code =", code)
            return ""
        return rsp_dict.get("tenant_access_token", "")

    def send_message(self, token, open_id, chat_id, text):
        url = "https://open.feishu.cn/open-apis/message/v4/send/"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }
        req_body = {
            "open_id": open_id,
            "chat_id": chat_id,
            "msg_type": "text",
            "content": {
                "text": text
            }
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("send message error, code = ", code, ", msg =", rsp_dict.get("msg", ""))

    def getChatGroupList(self, token):
        url = "https://open.feishu.cn/open-apis/chat/v4/list"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }
        req_body = {
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return

        rsp_body = response.read().decode('utf-8')
        print(rsp_body)
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("send message error, code = ", code, ", msg =", rsp_dict.get("msg", ""))
        groups = rsp_dict["data"]["groups"]
        chatidlist = []
        for group in groups:
            print(group["chat_id"])
            chatidlist.append(group["chat_id"])
        return chatidlist

    def getSheetContent(self, token, sheettoken, sheetrange):
        url = "https://open.feishu.cn/open-apis/sheet/v2/spreadsheets/{}/values/{}".format(sheettoken, quote(sheetrange))
        url = url + "?dateTimeRenderOption=FormattedString"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }
        print(url)
        req = request.Request(url=url, headers=headers, method='GET')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e)
            return

        rsp_body = response.read().decode('utf-8')
        print(rsp_body)
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("send message error, code = ", code, ", msg =", rsp_dict.get("msg", ""))
        else:
            content = rsp_dict["data"]["valueRange"]["values"]
        return code, content
