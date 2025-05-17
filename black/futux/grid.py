#!/usr/bin/python3

import logging, time, pandas, threading, numpy, math, datetime
import model, config
import futu

_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class Grid(threading.Thread):
    quote_ctx = None
    grid_config = None
    
    def __init__(self, quote_ctx, grid_config):
        threading.Thread.__init__(self)
        self.quote_ctx = quote_ctx
        self.grid_config = grid_config

    def run(self):
        code = self.grid_config.code

        logging.info('grid run, code:{}'.format(code))

        # 先订阅股票
        ret_sub, err_message = self.quote_ctx.subscribe([code], [futu.SubType.ORDER_BOOK], subscribe_push=False)
        if ret_sub != futu.RET_OK:
            logging.info('订阅股票[{}]失败: {}'.format(code, err_message))
            return

        logging.info('订阅股票成功{}'.format(code))

        # 订阅k线
        ret_sub, err_message = self.quote_ctx.subscribe([code], [futu.SubType.K_DAY], subscribe_push=False)
        if ret_sub != futu.RET_OK:
            logging.info('订阅股票K线[{}]失败: {}'.format(code, err_message))
            return

        logging.info('订阅股票K线成功{}'.format(code)) 


        trade_ctx = config.TradeContext.get_context(code)
        if trade_ctx is None:
            return

        while True:
            time.sleep(1)

            # 获取盘状态
            state, ret = Util.get_market_state(self.quote_ctx, code)
            if not ret:
                time.sleep(30)
                continue
            elif state not in [futu.MarketState.MORNING, futu.MarketState.AFTERNOON]:
                time.sleep(60)
                continue

            bid, ask, ret = Util.get_order_book_price(self.quote_ctx, code)
            if not ret:
                continue

            #
            buy_thread = BuyThread(self.quote_ctx, trade_ctx, self.grid_config, ask)
            sell_thread = SellThread(self.quote_ctx, trade_ctx, self.grid_config, bid)

            buy_thread.start()
            sell_thread.start()


            buy_thread.join()
            sell_thread.join()

            time.sleep(10.5)


class BuyThread(threading.Thread):
    cfg = None
    quote_ctx = None
    trade_ctx = None
    last_price = 0.00

    def __init__(self, quote_ctx, trade_ctx, cfg:config.GridConfig, last_price):
        threading.Thread.__init__(self)
        self.cfg = cfg
        self.quote_ctx = quote_ctx
        self.trade_ctx = trade_ctx
        self.last_price = last_price

    def run(self):
        # 当前价比最高限价要高，不购买
        if self.cfg.hight_price > 0 and self.last_price > self.cfg.hight_price:
            logging.debug('当前价比最高限价要高，忽略购买, hight-price:{}, curr-price:{}'.format(self.cfg.hight_price, self.last_price))
            return

        # 当前最低价比最低限价要低，不购买
        if self.cfg.low_price > 0 and self.last_price < self.cfg.low_price:
            logging.debug('当前价比最低限价要低，忽略购买, low-price:{}, curr-price:{}'.format(self.cfg.low_price, self.last_price))
            return 

        # 获取当前最低价记录
        row = model.GridModel.select().where(model.GridModel.futu_id==config.FutuConfig.futu_id, 
            model.GridModel.code==self.cfg.code, 
            model.GridModel.status.in_([10, 20])).order_by(model.GridModel.b_dealt_avg_price.asc()).first()

        if row is None:
            self.__buy_first()
        else:
            self.__buy_more(row)
        


    def __buy_first(self):
        if self.cfg.base_buy_type == 1:
            '''
                新建仓，当前低于30天平均，即买入
            '''
            ret, data = self.quote_ctx.get_cur_kline(self.cfg.code, 30, futu.SubType.K_DAY, futu.AuType.QFQ)
            if ret != futu.RET_OK:
                logging.info('获取k线数据失败{}, {}'.format(ret, data))
                return

            avg = numpy.average(data['open'])
            if avg <= 0:
                logging.warn('当前k线平均值为空, avg:{}'.format(avg))
                return

            # 当前价比平均价要高，不买入
            if avg < self.last_price:
                logging.debug('当前价比平均要高，忽略购买, curr-price:{}, avg:{}'.format(self.last_price, avg))
                return 
        elif self.cfg.base_buy_type == 2:
            '''
                新建仓，如果当前价低于设定价，即买入
            '''
            if self.last_price > self.cfg.base_buy_type2_hight_price:
                logging.debug('当前价比设定价要高，忽略购买, curr-price:{}, setting-price:{}'.format(self.last_price, self.cfg.base_buy_type2_hight_price))
                return
        else:
            return

        buy_qty = Util.get_buy_qty(self.trade_ctx, self.cfg, self.last_price)
        if buy_qty == 0:
            logging.info('获取余额为0, 不买入')
            return

        logging.info('买入建仓底, last-price:{}，buy-qty:{}'.format(self.last_price, buy_qty))


        res, data = Util.buy(self.trade_ctx, self.last_price, buy_qty, self.cfg.code)
        if not res:
            logging.warn('购买股票失败:{}'.format(data))
            return

        logging.info('购买股票成功,code:{}, price:{}, qty:{}'.format(self.cfg.code, self.last_price, buy_qty))

        nid = Util.order_add(self.cfg.code, self.last_price, buy_qty, data.get('order_id', ''))

        if nid > 0:
            logging.info('新建订单成功:{}'.format(nid))
            return

        logging.warn('新建订单失败:{}'.format(data))

        return

    def __buy_more(self, last):
        buy_price = self.last_price * (1 + self.cfg.buy_percent)
        if buy_price > last.b_dealt_avg_price:
            logging.debug('当前价比购买价格要高，忽略购买, curr-price:{}, last-price:{}, percent:{}, buy-price:{}'.format(
                self.last_price, last.b_dealt_avg_price, self.cfg.buy_percent, buy_price
            ))
            return

        logging.info('购买更多订单, current-price:{}, last-price:{}'.format(self.last_price, last.b_dealt_avg_price))

        buy_qty = Util.get_buy_qty(self.trade_ctx, self.cfg, self.last_price)
        if buy_qty == 0:
            logging.info('获取余额为0, 不买入')
            return

        res, data = Util.buy(self.trade_ctx, self.last_price, buy_qty, self.cfg.code)
        if not res:
            logging.warn('购买股票失败:{}'.format(data))
            return

        logging.info('购买股票成功,code:{}, price:{}, qty:{}'.format(self.cfg.code, self.last_price, buy_qty))

        nid = Util.order_add(self.cfg.code, self.last_price, buy_qty, data.get('order_id', ''))

        if nid > 0:
            logging.info('新建订单成功:{}'.format(nid))
            return

        logging.warn('新建订单失败:{}'.format(data))

        return


class SellThread(threading.Thread):
    cfg = None
    quote_ctx = None
    trade_ctx = None
    last_price = 0.00

    def __init__(self, quote_ctx, trade_ctx, cfg:config.GridConfig, last_price):
        threading.Thread.__init__(self)
        self.cfg = cfg
        self.quote_ctx = quote_ctx
        self.trade_ctx = trade_ctx
        self.last_price = last_price

    def run(self):
        self.__run_position()


    def __run_position(self):
        '''
            根据整个持仓收益来卖出
        '''        
        pass
        # 查出当前持仓收益
        data, ret = Util.position_list_query(self.trade_ctx, self.cfg.code)
        if not ret:
            return

        ratio = data.get('pl_ratio', 0.0)
        if ratio < (self.cfg.sell_percent*100):
            return


        sell_qty = data.get('can_sell_qty', 0)

        if sell_qty <= 0:
            return

        logging.info('卖出所有持仓股票, code:{}, qty:{}, can-sell-qty:{}, curr-price:{}'.format(
            self.cfg.code, 
            data.get('qty'),
            sell_qty,
            self.last_price,
        ))
        
        # 卖所有持仓
        res, data = Util.sell(self.trade_ctx, self.last_price, sell_qty, self.cfg.code)
        if not res:
            logging.warn('卖出股票失败, code:{}, msg:{}'.format(self.cfg.code, data))
            return

        logging.info('卖出持仓股票成功,code:{}, price:{}, qty:{}'.format(self.cfg.code, self.last_price, sell_qty))

        updated = model.GridModel.update(
            s_create_time=time.strftime(_TIME_FORMAT, time.localtime(time.time())),
            status=40,
            s_price=self.last_price,
            s_dealt_qty=self.last_price,
        ).where(
            model.GridModel.futu_id==config.FutuConfig.futu_id,
            model.GridModel.code==self.cfg.code,
            model.GridModel.status==20,
        ).execute()


    def __run_each(self):
        '''
            根据每个订单来判断是否卖出
        '''
        # 获取所有未售的订单列表
        not_sell_list = Util.get_not_sell_order_list(self.cfg.code)

        for row in not_sell_list:
            if row.status != 20:
                continue

            price = row.b_dealt_avg_price * (1 + self.cfg.sell_percent)
        
            # 如果需要卖的价格比当前要低，则忽略
            if self.last_price < price:
                continue

            res, data = Util.sell(self.trade_ctx, self.last_price, row.b_dealt_qty, self.cfg.code)
            if not res:
                logging.warn('卖出股票失败:{}'.format(data))
                continue

            logging.info('卖出股票成功,code:{}, price:{}, qty:{}'.format(self.cfg.code, self.last_price, row.b_dealt_qty))

            res = Util.order_update(row.id, 
                s_order_id=data.get('order_id', ''),
                s_qty=row.b_dealt_qty,
                s_price=self.last_price,
                s_create_time=time.strftime(_TIME_FORMAT, time.localtime(time.time())),
                status=30
            )

            time.sleep(3.8)


class Util:

    @staticmethod
    def accinfo_query(trade_ctx):
        '''
            获取账户信息
            return True, dict{}
        '''
        ret, data = trade_ctx.accinfo_query(config.FutuConfig.trd_env)
        if ret != futu.RET_OK:
            logging.info('获取账户信息失败{}, msg:{}'.format(ret, data))
            return False, None
        
        row = data.loc[0].to_dict()
        return True, row

    @staticmethod
    def get_buy_qty(trade_ctx, cfg, last_price):
        '''
            获取买入的金额
            return float
            如果为0,则为失败
        '''
        res, data = Util.accinfo_query(trade_ctx)
        if res is False:
            return 0

        total_price = cfg.buy_qty * last_price

        # 如果当前购买力资金比买入需要总资金要多，则购买
        if data.get('power', 0.00) >= total_price:
            return cfg.buy_qty

        return 0

    @staticmethod
    def buy(trade_ctx, price, qty, code):
        return Util.__place_order(trade_ctx, price, qty, code, futu.TrdSide.BUY, futu.OrderType.NORMAL, 0)

    @staticmethod
    def sell(trade_ctx, price, qty, code):
        return Util.__place_order(trade_ctx, price, qty, code, futu.TrdSide.SELL, futu.OrderType.NORMAL, 0)

    @staticmethod
    def __place_order(trade_ctx, price, qty, code, trd_side, order_type, adjust_limit):
        '''
            return bool, string/dict
        '''
        ret, data = trade_ctx.place_order(price=price, qty=qty, code=code, 
            trd_side=trd_side,
            order_type=order_type, 
            adjust_limit=adjust_limit, 
            trd_env=config.FutuConfig.trd_env, 
            time_in_force=futu.TimeInForce.DAY,
            remark='python 机器人交易 ^_^'
        )

        if ret != futu.RET_OK:
            return False, data

        return True, data.loc[0].to_dict()


    @staticmethod
    def order_add(code, price, qty, b_order_id):
        '''
            新添加一条订单记录到db
            return insert-id
        '''
        id = model.GridModel.insert(
            futu_id=config.FutuConfig.futu_id,
            code=code,
            status=10,
            b_order_id=b_order_id,
            b_price=price,
            b_qty=qty,
            b_create_time=time.strftime(_TIME_FORMAT, time.localtime(time.time())),
            b_dealt_qty=qty,
            b_dealt_avg_price=price
        ).execute()

        return id


    @staticmethod
    def order_update(id, **data):
        '''
            更新订单, id, **data
            return int,受影响行数
        '''
        updated = model.GridModel.update(**data).where(model.GridModel.id==id).execute()
        if updated == 1:
            logging.info('更新订单信息成功, id:{}'.format(id))
        else:
            logging.warn('更新订单信息异常, id:{}, updated:{}'.format(id, updated))
        return updated

    
    @staticmethod
    def get_not_sell_order_list(code):
        '''
            获取所有未售的订单列表
        '''
        ls = model.GridModel.select().where(model.GridModel.futu_id==config.FutuConfig.futu_id, 
            model.GridModel.code==code, 
            model.GridModel.status==20)

        return ls


    @staticmethod
    def get_order_book_price(quote_ctx, code, num=1):
        '''
            获得深度买入与卖出价
            return bid, ask, bool
        '''
        ret, data = quote_ctx.get_order_book(code, num)
        if ret !=futu.RET_OK:
            logging.error('获取摆盘数据出错, code:{}, ret:{}, msg:{}'.format(code, ret, data))
            return 0, 0, False

        bids = data.get('Bid', [])
        if len(bids) < 1:
            logging.warn('获取摆盘数据bid数据为空, code:{}, data:{}'.format(code, data))
            return 0, 0, False

        bid = bids[0][0]

        asks = data.get('Ask', [])
        if len(asks) < 1:
            logging.warn('获取摆盘数据ask数据为空, code:{}, data:{}'.format(code, data))
            return 0, 0, False

        ask = asks[0][0]

        if ask <= 0 or bid <= 0:
            return 0, 0, False

        return bid, ask, True


    @staticmethod
    def get_market_state(quote_ctx, code):
        '''
            获取股票当前状态
            return state, bool
        '''
        try:
            ret, data = quote_ctx.get_market_state([code])
            if ret != futu.RET_OK:
                logging.error('获取市场状态出错, ret:{}, msg:{}, code:{}'.format(ret, data, code))
                return '', False

            row = data.loc[0].to_dict()

            return row.get('market_state', ''), True
        except Exception as e:
            logging.exception('获取市场状态异常, code:{}, except:{}'.format(code, repr(e)))
            return '', False
            

    @staticmethod
    def  position_list_query(trade_ctx, code):
        '''
            获取持仓
            return dict, bool
        '''
        try:
            ret, data = trade_ctx.position_list_query(code=code, trd_env=config.FutuConfig.trd_env)
            if ret != futu.RET_OK:
                logging.error('获取持仓错误, ret:{}, msg:{}, code:{}'.format(ret, data, code))
                return {}, False

            if len(data) == 0:
                return {}, False
            row = data.loc[0].to_dict()

            return row, True
        except Exception as e:
            logging.exception('获取持仓异常, code:{}, exception:{}'.format(code, repr(e)))
            return {}, False


class GridWorkerThread(threading.Thread):
    '''
        更新订单状态
    '''

    # def __init__(self):
    #     threading.Thread.__init__(self)


    def run(self):
        while True:
            try:
                self.__run()
            except Exception as e:
                logging.exception(repr(e))

            time.sleep(30.5)


    def __run(self):
        ls = model.GridModel.select().where(model.GridModel.futu_id==config.FutuConfig.futu_id, 
            model.GridModel.status.in_([10, 30]))

        for row in ls:
            order_detail = self.__order_detail(row)
            if order_detail == None:
                time.sleep(8.4)
                continue

            if row.status == 10:
                self.__check_buy_order(row, order_detail)

            elif row.status == 30:
                self.__check_sell_order(row, order_detail)

            else:
                logging.warn('非法状态订单, id:{}, status:{}'.format(row.id, row.status))


            time.sleep(10.4)

    
    def __check_buy_order(self, row, order_detail):
        # 如果当前全部成交，则为成功
        order_status = order_detail.get('order_status', '')
        if order_status == futu.OrderStatus.FILLED_ALL:
            logging.info('购买订单全部成交, id:{}'.format(row.id))
            Util.order_update(row.id, 
                b_dealt_avg_price = order_detail.get('dealt_avg_price', 0.00),
                b_dealt_qty = order_detail.get('dealt_qty', 0.00),
                status = 20,
            )
            return

        # 全部取消
        cancel_status = [
            futu.OrderStatus.CANCELLED_ALL,
            futu.OrderStatus.FAILED,
            futu.OrderStatus.DISABLED,
            futu.OrderStatus.DELETED,
        ]
        if order_status in cancel_status:
            logging.info('购买订单取消, id:{}, status:{}'.format(row.id, order_status))
            Util.order_update(row.id, 
                b_dealt_avg_price = order_detail.get('dealt_avg_price', 0.00),
                b_dealt_qty = order_detail.get('dealt_qty', 0.00),
                status = 100,       # 整个订单取消, status=100
            )
            return

        # 暂时还没有实现超时后取消订单

    def __check_sell_order(self, row, order_detail):
        # 如果当前全部成交，则为成功
        order_status = order_detail.get('order_status', '')
        if order_status == futu.OrderStatus.FILLED_ALL:
            logging.info('卖出订单全部成交, id:{}'.format(row.id))
            Util.order_update(row.id, 
                s_dealt_avg_price = order_detail.get('dealt_avg_price', 0.00),
                s_dealt_qty = order_detail.get('dealt_qty', 0.00),
                status = 40,
            )
            return

        # 全部取消
        cancel_status = [
            futu.OrderStatus.CANCELLED_ALL,
            futu.OrderStatus.FAILED,
            futu.OrderStatus.DISABLED,
            futu.OrderStatus.DELETED,
        ]
        if order_status in cancel_status:
            logging.info('卖出订单取消, id:{}, status:{}'.format(row.id, order_status))
            Util.order_update(row.id, 
                status = 20, 
            )
            return

    def __order_detail(self, row):
        '''
            获得订单的远程
        '''
        oid = ''
        if row.status == 10:
            start = row.b_create_time
            oid = row.b_order_id
        elif row.status == 30:
            start = row.s_create_time
            oid = row.s_order_id
        else:
            return None

        try:

            e = start + datetime.timedelta(seconds=30)
            start = start + datetime.timedelta(seconds=-10)
            trade_ctx = config.TradeContext.get_context(row.code)
            if trade_ctx is None:
                return None
            ret, data = trade_ctx.history_order_list_query(
                trd_env=config.FutuConfig.trd_env,
                start=start.strftime(_TIME_FORMAT),
                end=e.strftime(_TIME_FORMAT),
                code=row.code
            )
            if ret != futu.RET_OK:
                logging.info('请求历史订单失败:{}'.format(data))
                return None

            datax = data.to_dict('records')
            for rowx in datax:
                if rowx.get('order_id', '') == oid:
                    return rowx
            
            return None

        except Exception as e:
            logging.exception(repr(e))
            return None
        
        return None 