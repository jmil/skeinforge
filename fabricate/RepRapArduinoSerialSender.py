#!/usr/bin/env python
# encoding: utf-8
"""
Created by Brendan Erwin on 2008-05-21.
Copyright (c) 2008 Brendan Erwin. All rights reserved.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""

import sys
import os
import serial
import time


class RepRapArduinoSerialSender:
	"""
		A utility class for communication with the Arduino from python.
		Intended for g-code only. Raises ValueException if the arduino
		returns an unexpected response. Usually caused by sending invalid
		g-code.
	"""
	
	_verbose = False
	
	def __init__(self, port, verbose=False):
		"""
			Opens the serial port and prepares for writing.
			port MUST be set, and values are operating system dependant.
		"""
		self._verbose = verbose

		if self._verbose:
			print >> sys.stdout, "Opening serial port: " + port
	
		#Timeout value 10" max travel, 1RPM, 20 threads/in = 200 seconds
		self.ser = serial.Serial(port, 19200, timeout=200)

		if self._verbose:
			print >> sys.stdout, "Serial Open?: " + str(self.ser.isOpen())
			print >> sys.stdout, "Baud Rate: " + str(self.ser.baudrate)
		
	def reset(self):
		"""
			Resets the arduino by droping DTR for 1 second
			This will then wait for a response ("ready") and return.
		"""
		#Reboot the arduino, and wait for it's response
		if self._verbose:
			print "reseting arduino..."

		self.ser.setDTR(0)
		# There is presumably some latency required.
		time.sleep(1)
		self.ser.setDTR(1)
		self.read("start")

	def write(self, block):
		"""
			Writes one block of g-code out to arduino and waits for an "ok".
			This will raise "ValueError" if it doesn't get an "ok" back.
			This routine also removes all whitespace before sending it to the arduino,
			which is handy for gcode, but will screw up if you try to do binary communications.
		"""
		if self._verbose:
			print block
		
		# The arduino GCode interperter firmware doesn't like whitespace
		# and if there's anything other than space and tab, we have other problems.
		block=block.strip()
		block=block.replace(' ','')
		block=block.replace("\t",'')
		#Skip blank blocks.
		if len(block) == 0:
			return

		self.ser.write(block)
		self.read("ok")

	def read(self, expect=None):
		"""
			This routine should never be called directly. It's used by write() and reset()
			to read a one-line response from the Arduino, and raise an exception if
			it doesn't contain the expected response.
		"""
		#The g-code firmware returns exactly ONE line per block of gcode sent.
		response = self.ser.readline().strip() 
		if expect is None:
			return

		if expect in response:
			if self._verbose:
				print response
		else:
			respone="Got non-ok reponse: \""+response + "\" when sending \"" + block + "\""
			print response
			raise ValueError(response)


	def close():
		"""
			Closes the serial port, terminating communications with the arduino.
		"""
		if self._verbose:
			print >> sys.stdout, "Closing serial port."
		self.ser.close()

		if self._verbose:
			print >> sys.stdout, "Serial Open?: " + str(self.ser.isOpen())
