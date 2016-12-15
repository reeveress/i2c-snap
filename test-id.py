import smbus

bus = smbus.SMBus(1)
addr = 0x50

bus.write_byte(addr,0)
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))
print ("%02x"%bus.read_byte(addr))

