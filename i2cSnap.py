import corr
import time

katcp_port = 7147
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



	def clockSpeed(self, inputSpeed, desiredSpeed):
		preScale = (inputSpeed/(5*desiredSpeed))-1
		#Clear EN bit in the control register before writing to prescale register
		self.fpga.write_int(self.controller_name, 0x00, offset = controlReg)
		#Write the preScale factor to the Prescale Register's low bit 
		self.fpga.write_int(self.controller_name, preScale, offset = PRERlo,blindwrite=True)



	def writeSlave(self,addr,data):
		#write address + write bit to Transmit Register, shifting to create bottom bit
		#to specify read/write operation
		self.fpga.write_int(self.controller_name, (addr<<1) , offset = transmitReg,blindwrite=True)
		
		
		#set STA bit
		self.fpga.write_int(self.controller_name, 0x80 , offset = commandReg,blindwrite=True)
		
		
		
		
		#set WR bit
		self.fpga.write_int(self.controller_name, 0x10 , offset = commandReg,blindwrite=True)

		
		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE, 0 when complete
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x02):
			time.sleep(.05)



		#read RxACK bit from status register, should be 0
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x80):
			time.sleep(.05)
		
		
		#write data to Transmit registrer
		self.fpga.write_int(self.controller_name, data, offset = transmitReg,blindwrite=True)
		


		#set STO bit
		self.fpga.write_int(self.controller_name, 0x40 , offset = commandReg,blindwrite=True)
		



		#set WR bit
		self.fpga.write_int(self.controller_name, 0x10 , offset = commandReg,blindwrite=True)
		
		
		##WAIT FOR INTERRUPT OR TIP FLAG TO NEGATE
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x02):
			time.sleep(.05)
		
		
		
		#read RxACK bit from Status register: should be 0
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x80):
			time.sleep(.05)



	def readSlave(self,slaveAddr, memLoc=0):
		#write address+write bit to transmit register
		self.fpga.write_int(self.controller_name, slaveAddr<<1 , offset = transmitReg,blindwrite=True)

		#set STA bit
		self.fpga.write_int(self.controller_name, 0x80 , offset = commandReg,blindwrite=True)

		#set WR bit
		self.fpga.write_int(self.controller_name, 0x10 , offset = commandReg,blindwrite=True)

		#wait for interrupt or TIP flag to negate
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x02):
			time.sleep(.05)


		#read RxACK bit from status register
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x80):
			time.sleep(.05)


		#write memory address to read from to Transmit register
		self.fpga.write_int(self.controller_name, memLoc , offset = transmitReg,blindwrite=True)

		
		#wait for interrupt or TIP flag to negate
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x02):
			time.sleep(.05)


		#read RxACK bit from status register
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x80):
			time.sleep(.05)


		#write address + read bit  to transmit register
		self.fpga.write_int(self.controller_name, (slaveAddr<<1)|0x01 , offset = transmitReg,blindwrite=True)

		#set STA bit
		self.fpga.write_int(self.controller_name, 0x80 , offset = commandReg,blindwrite=True)

		# set WR bit
		self.fpga.write_int(self.controller_name, 0x10 , offset = commandReg,blindwrite=True)

		#wait for interrupt or TIP flag to negate
		while not(self.fpga.read_int(self.controller_name, offset = statusReg)&0x02):
			time.sleep(.05)

		#set RD bit
		self.fpga.write_int(self.controller_name, 0x20 , offset = commandReg,blindwrite=True)


		#set ACK to 1(NACK)
		self.fpga.write_int(self.controller_name, 0x04 , offset = commandReg,blindwrite=True)

		#set STO bit
		self.fpga.write_int(self.controller_name, 0x40 , offset = commandReg,blindwrite=True)

		#return read value
		return self.fpga.read_int(self.controller_name, offset = receiveReg)

	
