#!/usr/bin/python3

#



import logging
import futu

class FutuConfig:
    host = "127.0.0.1"
    port = 11111

    trd_env = futu.TrdEnv.SIMULATE  # 模拟
    # trd_env = futu.TrdEnv.REAL      # 真实

    futu_id = 0
    trade_pwd_md5 = ''


    # futu_id = 0
    # trade_pwd_md5 = ''

class DbConfig:
    host = "127.0.0.1"
    port = 3306
    db = "futu_db"
    user = 'admin'
    pwd = 'admin'





class GridConfig:
    # 股票代码
    code = "HK.01810"

    # 交易 context
    trade_ctx = futu.OpenHKTradeContext


    # 每次买入的数量 ****
    buy_qty = 200

    # 购买价格百份比，比上一次低百份比后才买入
    buy_percent = 0.1
    # 卖出价格百份比
    sell_percent = 0.1


    # 最高价，高于此价不买入
    hight_price = 100
    # 最低价， 低于此价不买入
    low_price = 0



    # 购买仓底方式
    # 1: 当前价低于30天平均开盘价
    # 2: 手动设定最高价，低于此价即买入
    base_buy_type = 1
    
    # 最高价，低于此价即可买入
    base_buy_type2_hight_price = float(0)


    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


GridConfigs = [
    # GridConfig(),
    # GridConfig(code='HK.00700')

    # GridConfig(code='US.FUTU', trade_ctx=futu.OpenUSTradeContext, base_buy_type=2, base_buy_type2_hight_price=float(118), buy_qty=100),
    # GridConfig(code='US.RLX', trade_ctx=futu.OpenUSTradeContext, base_buy_type=2, base_buy_type2_hight_price=float(34.7), buy_qty=100),


    GridConfig(code='HK.01810', trade_ctx=futu.OpenHKTradeContext, base_buy_type=1, buy_qty=200),
]


# trade context
class _TradeContext:
    HK = None
    US = None
    HKCC = None
    CN = None
    # Future = None

    def init(self):
        '''
            初此化
            return bool
        '''
        cfg = {
            "HK": futu.OpenHKTradeContext,
            'US': futu.OpenUSTradeContext,
            'HKCC': futu.OpenHKCCTradeContext,
            'CN': futu.OpenCNTradeContext,
            # 'Future': futu.OpenFutureTradeContext,
        }

        for k in cfg:
            try:
                f = cfg[k]
                op = f(host=FutuConfig.host, port=FutuConfig.port, is_encrypt=None, security_firm=futu.SecurityFirm.FUTUSECURITIES)
                ret, data = op.unlock_trade('', FutuConfig.trade_pwd_md5.lower())
                if ret != futu.RET_OK:
                    logging.error('解锁交易失败{}, msg:{}'.format(ret, data))
                    return False

                setattr(self, k, op)
            except Exception as e:
                logging.exception(repr(e))
                return False

        return True


    def get_context(self, code):
        arr = code.split('.')
        if len(arr) != 2:
            logging.error('code 格式异常, code:{}'.format(code))
            return None

        code1 = arr[0].upper().strip()

        if code1 == 'HK':
            return self.HK
        elif code1 == 'US':
            return self.US
        elif code1 == 'HKCC':
            return self.HKCC
        elif code == 'CN':
            return self.CN
        # elif code1 == 'Future':
        #     return self.Future
        else:
            logging.error('code 格式异常, code:{}, code1:{}'.format(code, code1))
            return None



    def close(self):
        try:
            if self.HK:
                self.HK.close()

            if self.HKCC: 
                self.HKCC.close()

            if self.US:            
                self.US.close()

            # if self.Future:
            #     self.Future.close()

            if self.CN:
                self.CN.close()

        except Exception as e:
            logging.exception('关闭 trade context 异常:{}'.format(repr(e)))


TradeContext = _TradeContext()