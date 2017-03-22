import corr
import i2cSnap
import time

HOST = '10.1.0.23'
LED0_ADDR = 0x21
LED1_ADDR = 0x20

r = corr.katcp_wrapper.FpgaClient(HOST)
time.sleep(0.1)

i2c = i2cSnap.I2C(r, 'i2c_ant1')
i2c.clockSpeed(200)

i=0
while(True):
    i2c.write_byte(LED0_ADDR, i%256)
    i2c.write_byte(LED1_ADDR, i%256)
    i += 1
    time.sleep(0.05)



