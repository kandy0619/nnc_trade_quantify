#!/usr/bin/python3
#coding=utf-8

import pymysql
import sys
from GoldLine import GoldLine

db = pymysql.connect("localhost", "root", "", "futu")
print(sys.argv[1])
cursor = db.cursor()
lastmap = {}
sql = "select stockcode, date_format(time,'%Y-%m-%d'), last_close from kline_day where time>="+sys.argv[1]+" and stockcode='HK.00700'"
try:
	cursor.execute(sql)
	data = cursor.fetchall()
	for row in data:
		lastclose = row[2]
		lastmap[row[1]] = row[2]
except:
	print("Unexpected error:", sys.exc_info()[0])
sql = "select stockcode, date_format(time,'%Y-%m-%d'), open_price, close_price, high_price, low_price, last_close from kline_1min where time>"+sys.argv[1]+" and stockcode='HK.00700' order by time asc"
print(sql)


stratagy = GoldLine()
totalmoney = 100000
totalstock = 0
totalworth = 0
minmoney = 100000
count = 0
costprice = 0
hold_type = 0
try:
	cursor.execute(sql)
	data = cursor.fetchall()
	for row in data:
		time = row[1]
		lastclose = lastmap[time]
		checkpoint = row[2]
		res = stratagy.getOperation('00700', hold_type, lastclose, checkpoint)
		if res == 1:
			if totalstock<0:
				print("error: strategy is short when already long")
				break
			elif totalstock>0:
				continue
			buyamount = int(totalmoney / checkpoint /100)*100
			if buyamount == 0:
				continue
			totalstock = buyamount
			totalmoney = totalmoney - checkpoint * buyamount
			count = count+1
			costprice = checkpoint
			hold_type = 1
			print(row[1], "做多",checkpoint,totalmoney, totalstock, totalmoney + totalstock*checkpoint)
		elif res == 0:
			if totalstock>0:
				print("error: strategy is long when already short")
				break
			elif totalstock<0:
				continue
			buyamount = int(totalmoney / checkpoint /100)*100
			if buyamount == 0:
				continue
			totalstock = buyamount
			totalmoney = totalmoney - checkpoint * buyamount
			count = count + 1
			costprice = checkpoint
			hold_type = 2
			print(row[1], "做空",checkpoint,totalmoney, totalstock, totalmoney + totalstock*checkpoint)
		elif res == 2:
			if totalstock == 0:
				continue

			if hold_type == 2:
				profit = 0 - totalstock * (checkpoint - costprice)
			elif hold_type == 1:
				profit = totalstock * (checkpoint - costprice)

			totalmoney = totalmoney + totalstock * costprice +  profit
			totalstock = 0
			count = count+1
			totalworth = totalmoney
			hold_type = 0
			print(row[1], "平仓", checkpoint, totalmoney, profit)

			if totalmoney < minmoney:
				minmoney = totalmoney

except:
	print("Unexpected error:", sys.exc_info()[0])
print(totalworth, minmoney, count)
cursor.close()
db.close()
