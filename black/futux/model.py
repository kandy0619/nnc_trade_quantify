#!/usr/bin/python3

import peewee
import config

cfg = config.DbConfig
db = peewee.MySQLDatabase(cfg.db, user=cfg.user, password=cfg.pwd, port=cfg.port, host=cfg.host)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class GridModel(BaseModel):

    class Meta:
        table_name = 't_grid'


    id = peewee.BigAutoField(column_name="id", primary_key=True)
    futu_id = peewee.BigIntegerField(column_name="futu_id", default=0)
    code = peewee.CharField(column_name="code", default="")

    # 当前订单状态， 0初此
    # 10买入下单未成交， 20买入下单全部成交
    # 30卖出下单未成交，40卖出下单全部成交
    # 100买入撤单
    status = peewee.IntegerField(column_name="status", default=0)

    # buy
    b_order_id = peewee.CharField(column_name='b_order_id', default='')
    b_price = peewee.FloatField(column_name='b_price', default=0.00)
    b_qty = peewee.FloatField(column_name='b_qty', default=0.00)
    b_create_time = peewee.DateTimeField(column_name='b_create_time', default='2000-01-01 00:00:00')
    b_dealt_avg_price = peewee.FloatField(column_name='b_dealt_avg_price', default=0.00)
    b_dealt_qty = peewee.FloatField(column_name='b_dealt_qty', default=0.00)


    #sell
    s_order_id = peewee.CharField(column_name='s_order_id', default='')
    s_price = peewee.FloatField(column_name='s_price', default=0.00)
    s_qty = peewee.FloatField(column_name='s_qty', default=0.00)
    s_create_time = peewee.DateTimeField(column_name='s_create_time', default='2000-01-01 00:00:00')
    s_dealt_avg_price = peewee.FloatField(column_name='s_dealt_avg_price', default=0.00)
    s_dealt_qty = peewee.FloatField(column_name='s_dealt_qty', default=0.00)
