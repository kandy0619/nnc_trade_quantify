#!/usr/bin/python
#coding=utf-8


# 根据江恩理论 - 黄金分割线模型用来分析明确高点和低点的股票买入卖出位
class GoldLine:

	# 根据上一交易日的收盘价来判断明日的做多做空策略
	def analysisOperation(self, code, hold_type, num_pre, num_now):
		for l in rengong_point:
			if l[0] is code:
				# 如果上一交易日超出黄金分割线上下限，则返回-2
				if num_pre < l[1] or num_pre > l[6]:
					return -2;
				# 如果上一交易日落入0%~23.6%区间，0%上方或者突破23.6%做多，跌穿0%或者在23.6%下方平仓, 底部不做空；
				elif num_pre >= l[1] and num_pre < l[2]:
					if hold_type == 0:
						if (num_now >= l[1] and num_now < (l[1] + (l[1] * error))) or num_now > l[2] + l[2] * error:
							return 1;                                                               
						else:
							return -1;
					elif hold_type == 1:
						if num_now < l[2] and num_now > (l[2] - (l[2] * error)) or num_now <l[1]:
							return 2;
						else:
							return -1;
					elif hold_type == 2:
						if (num_now >= l[1] and num_now < (l[1] + (l[1] * error))) or num_now > l[2] + l[2] * error:
							return 2;
						else:
							return -1;
				# 如果上一交易日落入23.6%~38.2%区间；  
				elif num_pre >= l[2] and num_pre < l[3]:
					if hold_type == 0:
						#print '2空仓';
						if (num_now >= l[2] and num_now < (l[2] + (l[2] * error))) or num_now > l[3] + l[3] * error:
							#print '2买入';
							return 1;
						elif num_now < l[2] - l[2] * error or (num_now < l[3] and num_now > (l[3] - l[3] * error)):
							#print '2卖出';
							return 0;
						else:
							#print '2不操作';
							return -1;
					elif hold_type == 1:
						if num_now < l[2] - l[2] * error or (num_now < l[3] and num_now > (l[3] - l[3] * error)):
							#print '2平仓';
							return 2;
						else:
							#print '2不操作';
							return -1;
					elif hold_type == 2:
						if (num_now >= l[2] and num_now < (l[2] + (l[2] * error))) or num_now > l[3] + l[3] * error:
							#print '2平仓';
							return 2;
						else:
							#print '2不操作';
							return -1;
				# 如果上一交易日落入38.2%~50%区间； 
				elif num_pre >= l[3] and num_pre < l[4]:
					if hold_type == 0:
						#print '3空仓';
						if (num_now >= l[3] and num_now < (l[3] + (l[3] * error))) or num_now > l[4] + l[4] * error:
							#print '3买入';
							return 1;
						elif num_now < l[3] - l[3] * error or (num_now < l[4] and num_now > (l[4] - l[4] * error)):
                                			#print '3卖出';
							return 0;
						else:
							#print '3不操作';
							return -1;
					elif hold_type == 1:
						if num_now < l[3] - l[3] * error or (num_now < l[4] and num_now > (l[4] - l[4] * error)):
							#print '3平仓';
							return 2;
						else:
							#print '3不操作';
							return -1;
					elif hold_type == 2:
						if (num_now >= l[3] and num_now < (l[3] + (l[3] * error))) or num_now > l[4] + l[4] * error:
							#print '3平仓';
							return 2;
						else:
							#print '3不操作';
							return -1;
				# 如果上一交易日落入50%~61.8%区间
				elif num_pre >= l[4] and num_pre < l[5]:
					if hold_type == 0:
						if (num_now >= l[4] and num_now < (l[4] + (l[4] * error))) or num_now > l[5] + l[5] * error:
							#print '4买入';
							return 1;
						elif num_now < l[4] - l[4] * error or (num_now < l[5] and num_now > (l[5] - l[5] * error)):
							#print '4卖出';
							return 0;
						else:
							#print '4不操作';
							return -1;
					elif hold_type == 1:
						if num_now < l[4] - l[4] * error or (num_now < l[5] and num_now > (l[5] - l[5] * error)):
							#print '4平仓';
							return 2;
						else:
							#print '4不操作';
							return -1;
					elif hold_type == 2:
						if (num_now >= l[4] and num_now < (l[4] + (l[4] * error))) or num_now > l[5] + l[5] * error:
							#print '4平仓';
							return 2;
						else:
							#print '4不操作';
							return -1;
				# 如果上一交易日落入61.8%~100%区间，顶部不做多； 
				elif num_pre >= l[5] and num_pre < l[6]:
					if hold_type == 0:
						if num_now >= l[5] and num_now < (l[5] + (l[5] * error)):
							return 1;
						elif num_now < l[5] - l[5] * error or (num_now < l[6] and num_now > (l[6] - l[6] * error)):
							return 0;
						else:
							return -1;
					elif hold_type == 1:
						if num_now < l[5] - l[5] * error or (num_now < l[6] and num_now > (l[6] - l[6] * error)):
							return 2;
						else:
							return -1;
					elif hold_type == 2:
						if (num_now >= l[5] and num_now < (l[5] + (l[5] * error))) or num_now > l[6] + l[6] * error:
							return 2;
						else:
							return -1;

	# 对外暴露的方法，传入参数
	# code: string类型，是指对应的股票代码
	# hold_type: int类型，0表示无持仓，1表示当前持有多单，2表示当前持有空单
	# num_pre: float类型，是指上个交易日收盘价格
	# num_now: float类型，是指当前实时交易价格
	# 返回值：result，int类型：0 买入空单， 1 买入多单，2 平仓， -1 不操作, -2 超出范围
	def getOperation(self, code, hold_type, num_pre, num_now):
		result = self.analysisOperation(code, hold_type, num_pre, num_now);
		#print '股票代码' +  code + '在当前价位' + str(num_now) +  '的建议操作是：' + str(result);
		return result;

# 记录制定股票的区间最高点、最低点
rengong_point = [['800000', 25540.6, 26651.3, 27957, 29012, 30067.7,33484.1], 
                ['00700', 250.4, 303, 336, 362.6, 389, 474.7], 
                ['01093', 9.72, 13.6, 16, 18, 20, 26.42 ], 
                ['01177', 4.51, 6.71, 8.08, 9.18, 10.28, 13.86]];

# 允许0.5%的误差，单次允许最大亏损 = 2 * error
error = 0.005;
