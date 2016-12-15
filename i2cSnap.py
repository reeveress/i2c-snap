import time

PRERlo = 0
PRERhi = 1
controlReg = 2
transmitReg = 3
receiveReg = 3
statusReg = 4
commandReg = 4



class I2C:

	def __init__(self,fpga,controller_name):
		self.fpga = fpga
		self.controller_name = controller_name
                self.enable_core()



	def clockSpeed(self, desiredSpeed, inputSpeed = 100):
		preScale = (inputSpeed/(5*desiredSpeed))-1
		#Clear EN bit in the control register before writing to prescale register
		self.fpga.write_int(self.controller_name, 0x00, offset = controlReg)
		#Write the preScale factor to the Prescale Register's low bit 
		self.fpga.write_int(self.controller_name, preScale, offset = PRERlo,blindwrite=True)

	def getStatus(self):
		status = self.fpga.read_int('i2c_ant1', offset = statusReg)
		statusDict = {"ACK":{"desc":'Acknowledge from Slave',"val" : (status >> 7) &1}, "BUSY" : {"val" : (status >> 6)&1 , "desc" : 'Busy i2c bus'}, 'ARB' : {"val": (status >> 5)&1, "desc":'Lost Arbitration'}, "TIP" : {"val":(status>>1)&1,"desc":'Transfer in Progress'}, "INT": {"desc" : 'Interrupt Pending', "val" : status&1}}
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

	def _strobeStopBit(self):
		"""
		Toggle stop bit to indicate end of transmission
		"""
		self.fpga.write_int(self.controller_name, 0x40 , offset = commandReg,blindwrite=True)
		

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
		while self.getStatus()["ACK"]["val"]:
			time.sleep(.05)
		
		
		#write data to Transmit registrer
		self.fpga.write_int(self.controller_name, data, offset = transmitReg,blindwrite=True)
		


		#set STO bit
		self._strobeStopBit()



		#set WR bit
		self._strobeWriteBit()
		
		
		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while (self.getStatus()["TIP"]["val"]):
			time.sleep(.05)



		#read RxACK bit from status register, should be 0
		while self.getStatus()["ACK"]["val"]:
			time.sleep(.05)


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
		self.fpga.write_int(self.controller_name, 0x20 , offset = commandReg,blindwrite=True)


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
	
