import time
import json
import pymysql

class StockInfo:
	def __init__(self, code, d5, d10, d15, d20):
		self.code = code
		self.d5 = d5
		self.d10 = d10
		self.d15 = d15
		self.d20 = d20
db = pymysql.connect("localhost", "root", "", "futu")
cursor = db.cursor()
#严格检查(针对前一天升放量跌缩量)
def checkStockStrict(data):
	lastvolume = 0
	result = True
	for loop in reversed(range(len(data))):
		curvolume = data[loop][2]
		#跌，看是否缩量
		if (data[loop][0]> data[loop][1]):
			if (lastvolume > 0):
				if (lastvolume < curvolume):
#					print('跌放量：', data[loop])
					result = False
					break
		if (data[loop][0] < data[loop][1]):
			if (lastvolume > 0):
				if (lastvolume > curvolume):
#					print('涨缩量：', data[loop])
					result = False
					break
		lastvolume = curvolume
	return result
#宽松检查(哎时间段内升的成交量比跌的成交量高)
def checkStockLoose(data):
	result = True
	upsum = 0
	downsum = 0
	upcount = 0
	downcount = 0
	for loop in reversed(range(len(data))):
		curvolume = data[loop][2]
		#跌，看是否缩量
		if (data[loop][0]> data[loop][1]):
			#跌
			downsum = downsum + curvolume
			downcount = downcount + 1
		if (data[loop][0] < data[loop][1]):
			#涨
			upsum = upsum + curvolume
			upcount = upcount + 1
	#成交总量买量要大于卖量
	if (upsum<downsum):
		return 0
	upaverage = 0
	if (upcount>0):
		upaverage = upsum/upcount
	downaverage = 0
	if (downcount>0):
		downaverage = downsum/downcount
	if downaverage == 0:
		return 0
	return (upaverage-downaverage)/downaverage

sql = "select distinct(stockcode) from kline_day"
cursor.execute(sql)
stocklist = cursor.fetchall()
StockInfoList = []
for stock in stocklist:
	print(stock[0])
	sql = "select open_price,close_price, volume, to_days(time) as days from kline_day where stockcode='"+stock[0]+"' order by time desc limit 0,21"
	cursor.execute(sql)
	data = cursor.fetchall()
#	print(stock[0], '严格', checkStockStrict(data[0:5]), checkStockStrict(data[0:10]),checkStockStrict(data[0:15]),checkStockStrict(data[0:20]))
	d5 = checkStockLoose(data[0:5])
	d10 = checkStockLoose(data[0:10])
	d15 = checkStockLoose(data[0:15])
	d20 = checkStockLoose(data[0:20])
	StockInfoList.append(StockInfo(stock[0], d5, d10,d15,d20))
	print(stock[0], '宽松', checkStockLoose(data[0:5]), checkStockLoose(data[0:10]),checkStockLoose(data[0:15]),checkStockLoose(data[0:20]))
print("===================================================")
print("一周选股")
StockInfoList.sort(key=lambda x:x.d5, reverse=True)
for tempinfo in StockInfoList:
	if (tempinfo.d5<=0):
		break
	print(tempinfo.code, int(tempinfo.d5*10000)/100.0)
print("===================================================")
print("二周选股")
StockInfoList.sort(key=lambda x:x.d10, reverse=True)
for tempinfo in StockInfoList:
	if (tempinfo.d10<=0):
		break
	print(tempinfo.code, int(tempinfo.d10*10000)/100.0)
print("===================================================")
print("三周选股")
StockInfoList.sort(key=lambda x:x.d15, reverse=True)
for tempinfo in StockInfoList:
	if (tempinfo.d15<=0):
		break
	print(tempinfo.code, int(tempinfo.d15*10000)/100.0)
print("===================================================")
print("四周选股")
StockInfoList.sort(key=lambda x:x.d20, reverse=True)
for tempinfo in StockInfoList:
	if (tempinfo.d15<=0):
		break
	print(tempinfo.code, int(tempinfo.d20*10000)/100.0)

cursor.close()
db.close()
