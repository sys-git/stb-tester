'''
Created on 8 Nov 2012

@author: francis
'''
from decimal import Decimal
import time

def timestamp(t):
    return time.strftime("%%Y-%%m-%%d %%H:%%M:%%S.%(MS)s"%{"MS":str(Decimal(t)).split(".")[1][:6]}, time.localtime(t))

def truncateInteger(t, places=3):
    i = str(Decimal(t)).split(".")
    if places<1:
        places = 1
    return i[0]+"."+i[1][:places]
