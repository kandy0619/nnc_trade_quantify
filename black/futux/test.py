#!/usr/bin/python3

import math


def fee(total:float):
    yj = total * 0.0003
    if yj < 3:
        yj = 3

    xt = 0.5

    jsf = total * 0.00002
    if jsf < 2:
        jsf = 2
    if jsf > 100:
        jsf = 100

    yhs = math.ceil(total * 0.001)

    jyf = total * 0.00005

    jyzf = total * 0.000027


    print(yj, xt, jsf, yhs, jyf, jyzf)

    print('->>>>', yj+xt+jsf+yhs+jyf+jyzf + 15)

    

fee(3008)
