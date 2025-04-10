#!/usr/bin/env python3

# only for testing

import lib.pzem016 as pzem016
from lib.pzem016 import registers as reg

print("\r\n -------------------------------------------")
print(    " ---------- PZEM-0016 RS-485 Test ----------")
print(    " ------------------------------------------- \r\n")
print ("Author: dvestezar")

# aktuální čas
print("Current time:")
import datetime
now = datetime.datetime.now()
print(now.strftime("%Y-%m-%d %H:%M:%S"))


m=pzem016.masterData()
# pzem016.debug = True
pzem016.addr_default = 4

a=m.requestData()
print( '  >>>>>   rq all data','OK' if a else ' !!! Fail !!!' )
if a:
    print(m.__str__())

# print( '  >>>>>   rq all data','OK' if m.requestData(regId=reg.frequency) else ' !!! Fail !!!' )
# print( '  >>>>>   rq all data','OK' if m.resetEnergy() else ' !!! Fail !!!' )

# print('  >>>>>   rq set motbus adr','OK' if m.setModBusAddr(4) else ' !!! Fail !!!' )

a=m.getModbusAddr(None)
print('  >>>>>   rq GETt motbus adr from general addr = ',a if not a is None else ' !!! Fail !!!' )

print(" ---- EOF PZEM-0016 ----")

