"""
	File Name: packet.py
	File Creator: p1usj4de
	File Description: defines the packet structure
"""

#constants

# time of live of the packet
class Packet:

	DEFAULT_TTL = 256
	BROADCAST_ADDRESS = 1024


	def __init__(self, source, dest, payload, idPacket, ack=None, ttl=None):
		# the original packet structure
		self.source = source
		self.dest = dest
		self.payload = payload
		# to avoid misunderstanding, this field should be corrected to sequence, but I do not have enough time to do this
		self.id = idPacket
		self.ack = ack
		self.delay = 0.0

		# new-added area, for detection of the wormhole attack
		self.hopcount = 0
		self.markId = None # this area has been deprecated
		self.precedingId = None
		self.MAC = None
		self.alertMessage = False

		if ttl is None:
			self.ttl = Packet.DEFAULT_TTL

	def __str__(self):
		if self.ack:
			return "%d->%d %d hop:%d ack:%d %s" % (self.source, self.dest, self.hopcount, self.id, self.ack, self.payload)
		else:
			return "%d->%d %d None %s" % (self.source, self.dest, self.id, self.payload)

	def debug_str(self):
		markId = str(self.markId) if self.markId is not None else "none"
		precedingId = str(self.precedingId) if self.precedingId is not None else "none"
		return "%d->%d mark %s preceding %s" % (self.source, self.dest, markId, precedingId)

	def decrease_ttl(self):
		self.ttl -= 1

	def alive(self):
		if self.ttl < 0:
			return False
		else:
			return True

	# functions for wormhole detection
	def has_marked(self):
		if self.markId is not None:
			return True
		return False

	def mark_preceding(self, precedingId):
		self.precedingId = precedingId

	def mark_MAC(self, MAC):
		self.MAC = MAC

	def mark_id(self, markId):
		self.markId = markId

	def test_mark_id(self):
		if self.markId is not None:
			return True
		else:
			return False

	def test_preceding(self):
		if self.precedingId is not None:
			return True
		else:
			return False

	def test_MAC(self):
		# verify the packet's integrity, now we deprecate this method first
		return True

	def test_alert(self):
		return self.alertMessage

	def mark_alert(self):
		self.alertMessage = True

	# functions about request route query and response
	@staticmethod
	def generate_RQ_packet(source, dest, idPacket, queryDest):
		return Packet(source, dest, "ROUTE_QUERY for " + str(queryDest), idPacket)

	@staticmethod
	def test_RQ_packet(packet):
		if packet.payload.startswith("ROUTE_QUERY for "):
			return int(packet.payload[16:])
		else:
			return None

	@staticmethod
	def generate_RR_packet(source, dest, queryDest, idPacket, latency, nextPort, ack):
		return Packet(source, dest, "ROUTE_RESPONSE for %d NEXT %d LATENCY %f" % (queryDest, nextPort, latency), idPacket, ack)

	@staticmethod
	def test_RR_packet(packet):
		res = packet.payload.split(" ")
		if res[0] == "ROUTE_RESPONSE":
			return {"dest": int(res[2]), "next": int(res[4]), "latency": float(res[6])}
		else:
			return None

	@staticmethod
	def test_bc_packet(packet):
		if packet.dest == Packet.BROADCAST_ADDRESS:
			return True
		else:
			return False

	####################################################################
	# NOTES: SMR AND SMRR HAS BEEN REPLACE BY PHYSICAL
	# LAYER'S TECHNIQUE, SO ALL THE FUNCTIONS BELOW ABOUT
	# SMR AND SMRR SHOULD NOT BE USED
	####################################################################

	# functions about request for send message
	@staticmethod
	def generate_SMR_packet(source, dest, idPacket):
		return Packet(source, dest, "SMR_ASK FOR SPEAKING", idPacket, None)

	@staticmethod
	def test_SMR_packet(packet):
		if packet.payload == "SMR_ASK FOR SPEAKING":
			return True
		else:
			return False

	@staticmethod
	def generate_SMRR_OK_packet(source, dest, idPacket, ack):
		return Packet(source, dest, "SMR_OK", idPacket, ack)

	@staticmethod
	def generate_SMRR_DENIED_packet(source, dest, idPacket, ack):
		return Packet(source, dest, "SMR_DENIED", idPacket, ack)

	@staticmethod
	def test_SMRR_packet(packet):
		if packet.ack and (packet.payload == "SMR_OK" or packet.payload == 'SMR_DENIED'):
			return True
		else:
			return False

	@staticmethod
	def test_SMRR_OK_packet(packet):
		if packet.payload == "SMR_OK":
			return True
		else:
			return False

