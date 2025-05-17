#!/bin/sh
date >> /tmp/filter.log
echo "new task" >> /tmp/filter.log
python3 /home/jiangqiquan/jqq/autotrader/Cron/filter.py &>>/tmp/filter.log
python3 /home/jiangqiquan/jqq/autotrader/Cron/GetSnapshotUS.py &>>/tmp/filter.log
python3 /home/jiangqiquan/jqq/autotrader/Cron/getkline_us.py &>>/tmp/filter.log
python3 /home/jiangqiquan/jqq/autotrader/Cron/check34.py &>>/tmp/filter.log
python3 /home/jiangqiquan/jqq/autotrader/Cron/GetOptions.py &>>/tmp/filter.log
sort -rn -k2 /home/jiangqiquan/jqq/autotrader/Cron/result_list.txt|awk '{print $1}' >/home/jiangqiquan/jqq/autotrader/Cron/options_filter_stock.txt
echo "task end" >>/tmp/filter.log
