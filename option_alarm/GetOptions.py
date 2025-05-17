from futu import *
import sys
import time
import pymysql
import datetime
from larkapi import RequestHandler


# 实例化行情上下文对象
SysConfig.set_proto_fmt(ProtoFMT.Json)
quote_ctx = OpenQuoteContext(host="127.0.0.1", port=11111)

# 上下文控制
quote_ctx.start()              # 开启异步数据接收
quote_ctx.set_handler(TickerHandlerBase())  # 设置用于异步处理数据的回调对象(可派生支持自定义)
def GetOption():
    db = pymysql.connect(host="localhost", user="root", password="", db="futu", charset="utf8")
    cursor = db.cursor()
    access_token = RequestHandler.get_tenant_access_token(None)
    chatidlist = RequestHandler.getChatGroupList(None, access_token)

    start_date = (datetime.date.today()+datetime.timedelta(days=270)).strftime('%Y-%m-%d')
    print('start_date='+start_date)
    fin = open('/home/jiangqiquan/jqq/autotrader/Cron/options_filter_stock.txt', 'r')
    data_filter = OptionDataFilter()
    data_filter.open_interest_min = 2000
    stock_list = []
    for line in fin.readlines():
        stock_list.append(line.strip()) 
    stock_list.append('US.AAPL')
    text = "今日满足要求期权：\n"
    for code in stock_list:
        print('code:{}'.format(code))
        cursor.execute('select highest52weeks_price from snapshot where stockcode="'+code+'"')
        result = cursor.fetchall()
        if len(result) == 0:
            print('error code: {} do not have snapshot'.format(code))
            continue
        high_price = result[0][0]
        ret, data = quote_ctx.get_option_chain(code=code, start=start_date, option_type=OptionType.CALL, data_filter=data_filter)
        options_list = []
        if ret != RET_OK:
            print('get option chain failed:{}'.format(data))
        else:
            for loop in range(len(data['code'])):
                print('code:{} strike_price:{} D:{}'.format(data['code'][loop], data['strike_price'][loop], high_price))
                if float(data['strike_price'][loop]) > 0.8 * float(high_price):
                    options_list.append(data['code'][loop])
            ret1, data1 = quote_ctx.get_market_snapshot(options_list)
            if ret1 != RET_OK:
                print('get snapshot failed:{}'.format(data))
            else:
                print('snap:{}'.format(data1))
                for loopi in range(len(data1['code'])):
                    if data1['last_price'][loopi] < 1:
                        print('match code:{} price:{}'.format(data1['code'][loopi], data1['last_price'][loopi]))
                        line = "%s\t最新价:%.3f\t\n" % (data1['code'][loopi], data1['last_price'][loopi])
                        text = text + line
        time.sleep(3)
    for chatid in chatidlist:
            print(chatid)
            RequestHandler.send_message(None, access_token, "", chatid, text)
            print(text)

quote_ctx.close()  # 结束后记得关闭当条连接，防止连接条数用尽
