import corr
import i2cSnap
import time

HOST = '10.1.0.23'

r = corr.katcp_wrapper.FpgaClient(HOST)
time.sleep(0.1)

i2c = i2cSnap.I2C(r, 'i2c_ant1')
i2c.clockSpeed(100)

addr = 0x40

i2c.write_byte(addr, 0xe3)

time.sleep(0.01)

msb,lsb,crc = i2c.read_bytes(addr, 3)

val = (lsb + (msb  << 8)) & 0xfffc
temp = -46.85 + (val*175.72)/65536.0
print "Temp = %.2f" % temp

