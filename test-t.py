import smbus
import time
bus = smbus.SMBus(1)
addr = 0x40
data = [0,0,0,0]
bus.write_byte(addr,0xe3)
msb =  bus.read_byte(addr)
lsb = bus.read_byte(addr)
junk = bus.read_byte(addr)
val = (lsb + (msb  << 8)) & 0xfffc
temp = -46.85 + (val*175.72)/65536.0
print "Temp = %.2f" % temp

