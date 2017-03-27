import time

PRERlo = 0
PRERhi = 1
controlReg = 2
transmitReg = 3
receiveReg = 3
statusReg = 4
commandReg = 4

# I2C command
CMD_START = 1 << 7
CMD_STOP = 1 << 6
CMD_READ = 1 << 5
CMD_WRITE = 1 << 4
CMD_NACK = 1 << 3 # Not ACKnowledge, output 1 on SDA means release SDA and let VDD drives SDA high
CMD_IACK = 1 << 0 # interrupt ack, not supported

CORE_EN = 1 << 7 # i2c core enable
INT_EN = 1 << 6 # interrupt enable, not supported

WRITE_BIT = 0
READ_BIT = 1

class I2C:

	def __init__(self,fpga,controller_name):
		self.fpga = fpga
		self.controller_name = controller_name
                self.enable_core()

	def clockSpeed(self, desiredSpeed, inputSpeed = 100):
		"""
		Input speed in MHz and desired speed in kHz
		"""
		preScale = int((inputSpeed*1e3/(5*desiredSpeed))-1)
		#Clear EN bit in the control register before writing to prescale register
		self.disable_core()
		#Write the preScale factor to the Prescale Register's low bit 
		self.fpga.write_int(self.controller_name, (preScale >> 0) & 0xff, offset = PRERlo, blindwrite=True)
		#Write the preScale factor to the Prescale Register's high bit 
		self.fpga.write_int(self.controller_name, (preScale >> 8) & 0xff, offset = PRERhi, blindwrite=True)
		#Re-enable core
		self.enable_core()
	def readClockSpeed(self):
		lowBit = self.fpga.read_int(self.controller_name, offset = PRERlo)
		highBit = self.fpga.read_int(self.controller_name, offset = PRERhi)
		return (highBit << 8) + lowBit
	def getStatus(self):
		status = self.fpga.read_int(self.controller_name, offset = statusReg)
		statusDict = {
			"ACK"  : {"val" : (status >> 7) & 1, "desc" :'Acknowledge from Slave',},
			"BUSY" : {"val" : (status >> 6) & 1, "desc" : 'Busy i2c bus'},
			"ARB"  : {"val" : (status >> 5) & 1, "desc" :'Lost Arbitration'},
			"TIP"  : {"val" : (status >> 1) & 1, "desc" :'Transfer in Progress'},
			"INT"  : {"val" : (status >> 0) & 1, "desc" : 'Interrupt Pending'},
			}
		return statusDict
	
	def _strobeStartBit(self):
		"""
		Generate an i2c start signal for transmission/reception. This register automatically clears bits. 

		"""
		self.fpga.write_int(self.controller_name, 0x80 , offset = commandReg,blindwrite=True)
		
	def _strobeWriteBit(self):
		"""
		Toggle write bit to indicate that writing to slave is about to take place 
		"""
		self.fpga.write_int(self.controller_name, 0x10 , offset = commandReg,blindwrite=True)

	def _strobeReadBit(self):
		"""
		Toggle read bit to prepare slave for reading
		"""
		self.fpga.write_int(self.controller_name, 0x20 , offset = commandReg,blindwrite=True)

	def _strobeStopBit(self):
		"""
		Toggle stop bit to indicate end of transmission
		"""
		self.fpga.write_int(self.controller_name, 0x40 , offset = commandReg,blindwrite=True)

	def _strobeIACK(self):
		self.fpga.write_int(self.controller_name, 0x01, offset = commandReg, blindwrite=True)
	def writeSlave(self,addr,data):
		#write address + write bit to Transmit Register, shifting to create bottom bit
		#to specify read/write operation
		self.fpga.write_int(self.controller_name, (addr<<1) , offset = transmitReg,blindwrite=True)
		
		#set STA bit
		self._strobeStartBit()	
		
		#set WR bit
		self._strobeWriteBit()
		
		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.05)

		#read RxACK bit from status register, should be 0
		#while self.getStatus()["ACK"]["val"]:
		#	time.sleep(.05)
		
		#write data to Transmit registrer
		self.fpga.write_int(self.controller_name, data, offset = transmitReg,blindwrite=True)


		#set WR bit
		self._strobeWriteBit()
		
		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.05)
		#set STO bit
		self._strobeStopBit()

		#read RxACK bit from status register, should be 0
		#while self.getStatus()["ACK"]["val"]:
		#	time.sleep(.05)

	def readSlave(self,slaveAddr, memLoc=0):
		#write address+write bit to transmit register
		self.fpga.write_int(self.controller_name, (slaveAddr<<1)|0x01 , offset = transmitReg,blindwrite=True)

		#set STA bit
		self._strobeStartBit()

		#set WR bit
		self._strobeWriteBit()

		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.05)

		#read RxACK bit from status register, should be 0
		while self.getStatus()["ACK"]["val"]:
			time.sleep(.05)

		#write memory address to read from to Transmit register
		self.fpga.write_int(self.controller_name, memLoc , offset = transmitReg,blindwrite=True)

		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.05)

		#read RxACK bit from status register, should be 0
		while self.getStatus()["ACK"]["val"]:
			time.sleep(.05)

		#write address + read bit  to transmit register
		self.fpga.write_int(self.controller_name, (slaveAddr<<1)|0x01 , offset = transmitReg,blindwrite=True)

		#set STA bit
		self._strobeStartBit()

		# set WR bit
		self._strobeWriteBit()

		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.05)

		#set RD bit
		self._strobeReadBit()

		#set ACK to 1(NACK)
		self.fpga.write_int(self.controller_name, 0x04 , offset = commandReg,blindwrite=True)

		#set STO bit
		self._strobeStopBit()

		#return read value
		return self.fpga.read_int(self.controller_name, offset = receiveReg)

	def enable_core(self):
		"""
		Enable the wb-i2c core. Set the I2C enable bit to 1,
		Set the interrupt bit to 0 (disabled).
		"""
		I2C_ENABLE_OFFSET = 7
		self.fpga.write_int(self.controller_name, 1<<I2C_ENABLE_OFFSET, offset=controlReg)

	def disable_core(self):
		"""
		Disable the wb-i2c core. Set the I2C enable bit to 0,
		Set the interrupt bit to 0 (disabled).
		"""
		I2C_ENABLE_OFFSET = 7
		self.fpga.write_int(self.controller_name, 0<<I2C_ENABLE_OFFSET, offset=controlReg)

	def _write(self,addr,data):
		self.fpga.write_int(self.controller_name, data,	offset = addr, blindwrite=True)

	def _read(self,addr):
		return self.fpga.read_int(self.controller_name,	offset = addr)

	def write_byte(self,addr,data):
		"""
		addr: 8-bit integer
		data: 8-bit integer
		"""
		self._write(transmitReg,	(addr<<1)|WRITE_BIT)
		self._write(commandReg,		CMD_START|CMD_WRITE)
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.01)
		self._write(transmitReg,	data)
		self._write(commandReg,		CMD_WRITE|CMD_STOP)
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.01)
		
	def write_bytes(self,addr,data,hold=True):
		"""
		addr: 8-bit integer
		data: a list of 8-bit integers
                """
		# hold=True: write multiple bytes in one pair of I2C start and stop signals
		if hold:
			self._write(transmitReg,	(addr<<1)|WRITE_BIT)
			self._write(commandReg,		CMD_START|CMD_WRITE)
			while (self.getStatus()["TIP"]["val"]):
				time.sleep(.01)
			for i in range(len(data)):
				self._write(transmitReg,	data[i])
				self._write(commandReg,		CMD_WRITE)
				while (self.getStatus()["TIP"]["val"]):
					time.sleep(.01)
			self._write(commandReg,		CMD_STOP)
		# hold=False: issue multiple pairs of start and stop. Write one byte during each pair
		else:
			for i in range(len(data)):
				self.write_byte(addr,data[i])

	def read_byte(self,addr):
		"""
		addr: 8-bit integer
		"""
		self._write(transmitReg,	(addr<<1)|READ_BIT)
		self._write(commandReg,		CMD_START|CMD_WRITE)
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.01)
		self._write(commandReg,		CMD_READ|CMD_NACK|CMD_STOP)
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.01)
		return self._read(receiveReg)

	def read_bytes(self,addr,length,hold=True):
		"""
		addr: 8-bit integer
		length: the number of bytes needs to be read
                """
		data = []
		# hold=True: read multiple bytes in one pair of I2C start and stop signals
		if hold:
			self._write(transmitReg,	(addr<<1)|READ_BIT)
			self._write(commandReg,		CMD_START|CMD_WRITE)
			while (self.getStatus()["TIP"]["val"]):
				time.sleep(.01)
			for i in range(length-1):
				# The command below also gives an ACK signal from master to slave
				# because CMD_ACK is actually 0
				self._write(commandReg,		CMD_READ)
				ret = self._read(receiveReg)
				data.append(ret)
				while (self.getStatus()["TIP"]["val"]):
					time.sleep(.01)
			# The last read ends with a NACK (not acknowledge) signal and a STOP
			# from master to slave
			self._write(commandReg,		CMD_READ|CMD_NACK|CMD_STOP)
			ret = self._read(receiveReg)
			data.append(ret)
			while (self.getStatus()["TIP"]["val"]):
				time.sleep(.01)
		# hold=False: issue multiple pairs of start and stop. Read one byte during each pair
		else:
			for i in range(length):
				ret = self.read_byte(addr)
				data.append(ret)
		return data

