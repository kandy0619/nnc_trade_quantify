#!/usr/bin/python3

import logging, time, sys
import config, grid, model
import futu


def main():
    # logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)d [%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)d [%(levelname)s] %(message)s', level=logging.INFO)

    x = logging.getLogger('peewee')
    x.setLevel(logging.INFO)
    # logging

    try:
        quote_ctx = futu.OpenQuoteContext(host=config.FutuConfig.host, port=config.FutuConfig.port)
        
        if not config.TradeContext.init():
            return

        # 先启动 worker
        grid.GridWorkerThread().start()

        ts = []
        for gc in config.GridConfigs:
            t = grid.Grid(quote_ctx, gc)
            # t.setDaemon(True)
            t.start()
            ts.append(t)



        for t in ts:
            t.join()


    except Exception as e:
        logging.exception(repr(e))

    finally:
        quote_ctx.close()
        config.TradeContext.close()
    


if __name__ == '__main__':
    main()