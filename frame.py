"""
	File Name: frame.py
	File Creator: p1usj4de
	File Description: defines the physical layer's data -- frame
"""

import random

class Frame:
	def __init__(self, source, dest, packet, idFrame=None, ctlInfo=None, ack=None):
		self.source = source # the last person handle the packet
		self.dest = dest # the next person should handle the packet
		self.packet = packet # physical layer's payload

		if not idFrame:
			self.idFrame = random.randint(0, 100000)
		else:
			self.idFrame = idFrame

		self.ctlInfo = ctlInfo
		self.ack = ack

	@staticmethod
	def generate_speaking_beacon(source, dest, idFrame):
		return Frame(source, dest, None, idFrame, "SPEAKING")

	@staticmethod
	def generate_speaking_reply(source, dest, ack, reply):
		if reply:
			return Frame(source, dest, None, ctlInfo="SPEAKING_REPLY YES", ack=ack)
		else:
			return Frame(source, dest, None, ctlInfo="SPEAKING_REPLY NO", ack=ack)

	@staticmethod
	def test_speaking_beacon(frame):
		if frame.ctlInfo == "SPEAKING" and frame.packet is None:
			return frame.idFrame
		else:
			return None

	@staticmethod
	def test_speaking_reply(frame):
		if frame.ctlInfo == "SPEAKING_REPLY YES":
			return True
		elif frame.ctlInfo == "SPEAKING_REPLY NO":
			return False
		else:
			return None