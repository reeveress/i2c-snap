import corr
import i2cSnap
import time

HOST = '10.1.0.23'
addr = 0x50

r = corr.katcp_wrapper.FpgaClient(HOST)
time.sleep(0.1)

i2c = i2cSnap.I2C(r, 'i2c_ant1')
i2c.clockSpeed(100)

i2c.write_byte(addr, 0)
print i2c.read_bytes(addr,8)
