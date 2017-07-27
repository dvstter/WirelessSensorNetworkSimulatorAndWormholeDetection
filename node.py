"""
	File Name: node.py
	File Creator: p1usj4de
	File Description: defines the basic node class and wormhole class
"""

import math
from collections import deque
import time
from ncache import *
import sys

from packet import *
from frame import *
from routetbl import *
from topo import *

# constants
NEIGHBOR_DISTANCE_SQUARE = 100

# currently, these three value must be 0, so you should not modify this value
SINK_NODE_ID = 0
SINK_NODE_X = 0
SINK_NODE_Y = 0
RUNNING_INTERVAL = 3 # this number can change the node's running speed, more speed means need more powerful CPU

NODE_DEBUG = False # debug tag

# basic node type
class Node:
	FRAME_IN_PACKET = 0
	FRAME_DISCARD = 1
	FRAME_HAS_PROCESSED = 2

	PACKET_IN_PAYLOAD = 0
	PACKET_FORWARD = 1
	PACKET_HAS_PROCESSED = 2

	CONTINUE = 0
	DROP = 1

	# just for sink node constants
	NETWORK_INIT = 0
	NETWORK_STABLED = 1
	NETWORK_RESTABLED = 2
	NETWORK_CHANGED = 3

	def __init__(self, serial, x, y):
		# the physical location of the node
		self.x = x
		self.y = y

		# the number of the node
		self.serial = serial

		# the number of the packet
		self.idNext = int(random.random()*100)

		# neighbor node which can be accessed directly
		self.neighbors = []

		# temporarily store the latency of the neighbors
		self.latencies = []

		# route table
		self.table = RouteTable(self.serial)

		# the frame buffer
		self.buffer = deque(maxlen=130)

		# for carrier sense
		self.wantSpeak = False

		# frame's serial number just only for carrier sense
		self.carrierBasic = random.randint(0, 10000)

		# send message or not
		self.sendMessageFlag = True

		# make each node's interval different
		self.interval = RUNNING_INTERVAL + (random.randint(0, 10)) / 10 * RUNNING_INTERVAL

		# cache for wormhole detection
		self.cache = NodeCache(self.serial)

		# topology information for sink node
		self.topology = Topology()

		# some data structure just for sink node
		self.networkStatus = Node.NETWORK_INIT
		self.backupTopology = Topology()
		self.backupCache = NodeCache(self.serial)
		self.intermediateNodesNum = 0
		self.stabledNodes = set()
		self.networkStabledPromptDisplayOnlyOnce = False
		self.networkChangedPromptDisplayOnlyOnce = False
		self.networkRestabledPromptDisplayOnlyOnce = False

	def neighbor_add(self, anotherNode):
		distanceSquare = ( self.x - anotherNode.x ) ** 2 + ( self.y - anotherNode.y ) ** 2
		if distanceSquare <= NEIGHBOR_DISTANCE_SQUARE:
			self.neighbors.append(anotherNode)
			self.latencies.append(int(math.sqrt(distanceSquare)))

			if NODE_DEBUG:
				print str(self.serial) + "'s neighbor add " + str(anotherNode.serial)

	def neighbors_find(self, nodesList):
		# sink node should be able know the nodes' number
		if self.serial == SINK_NODE_ID:
			self.intermediateNodesNum = len(nodesList)
			self.intermediateNodesNum -= 1

		for each in nodesList:
			if each.serial == self.serial:
				continue
			self.neighbor_add(each)

	def get_neighbor(self, serial):
		for each in self.neighbors:
			if each.serial == serial:
				return each

		return None

	def get_neighbor_latency(self, serial):
		for idx in range(len(self.neighbors)):
			if self.neighbors[idx].serial == serial:
				return self.latencies[idx]

		# this code should not be executed, just for debug
		else:
			return None

	# -------------------------------------------------------------------
	# PHYSICAL LAYER
	# THIS LAYER PROCESS THE FRAME, NOT TOO MUCH WORK
	# -------------------------------------------------------------------
	def process_frame(self, frame):
		if self.BEFORE_FRAME(frame) == Node.DROP:
			return Node.FRAME_HAS_PROCESSED

		####################################################################
		# PROCESS CONTROL FRAME HERE
		####################################################################

		res = Frame.test_speaking_beacon(frame)
		if res:
			if not self.wantSpeak:
				tmpFrame = Frame.generate_speaking_reply(self.serial, frame.source, frame.idFrame, True)
			else:
				tmpFrame = Frame.generate_speaking_reply(self.serial, frame.source, frame.idFrame, False)

			self.get_neighbor(frame.source).receive(tmpFrame, self.get_neighbor_latency(frame.source))

			return Node.FRAME_HAS_PROCESSED

		res = Frame.test_speaking_reply(frame)
		if not res is None:
			# should do nothing here

			return Node.FRAME_HAS_PROCESSED


		####################################################################
		# PROCESS NORMAL FRAME HERE
		####################################################################

		# test bad frame
		if frame.dest != self.serial:
			return Node.FRAME_DISCARD
		else:
			return Node.FRAME_IN_PACKET

	#-------------------------------------------------------------------
	# NETWORK LAYER
	# NOTES: THE PACKET WILL BE PROCESSED HERE
	# IF RETURN PACKET_HAS_PROCESSED, THEN THE PACKET WILL BE DISCARD
	# IF RETURN PACKET_IN_PAYLOAD, THEN THE PAYLOAD WILL PASSED INTO
	#           APPLICATION LAYER
	# IF RETURN PACKET_FORWARD, THEN THE PACKET SHOULD BE FORWARD TO
	#           OTHER NODE
	#-------------------------------------------------------------------
	def process_packet(self, packet):
		if self.BEFORE_PACKET(packet) == Node.DROP:
			return Node.PACKET_HAS_PROCESSED

		self.process_packet_marking(packet) # intermediate node's procedure
		self.process_packet_parsing(packet) # sink node's procedure

		# test the packet is dead or alive
		# notes: this function in fact will never be processed, because in the receive() method
		# has processed this
		if not packet.alive():
			return Node.PACKET_HAS_PROCESSED

		# print some debug information
		if NODE_DEBUG:
			print "[*] " + str(self.serial) + " process_packet called. "
			print packet

		####################################################################
		# PROCESS CONTROL PACKET HERE
		####################################################################

		# process Send Message Request packet
		# this function has been deprecated
		if Packet.test_SMR_packet(packet):
			return Node.PACKET_HAS_PROCESSED

		# process Route Query packet
		requestDest = Packet.test_RQ_packet(packet)
		if requestDest is not None:
			# test if the table item existed
			if self.table.item_exist(requestDest):
				# if yes send a response
				nextPort = self.serial
				latency = self.table.get_latency(requestDest) + self.table.get_latency(packet.source)
				packet = Packet.generate_RR_packet(self.serial, packet.source, requestDest, self.idNext, latency, nextPort, packet.id)
				self.idNext += 1
				self.get_neighbor(packet.dest).receive(Frame(self.serial, packet.dest, packet), self.get_neighbor_latency(packet.dest))
			else:
				# if not send a query
				bcNum = len(self.neighbors) - 1
				for each in self.neighbors:
					if not each.serial == packet.source:
						each.receive(Frame(self.serial, each.serial, Packet.generate_RQ_packet(self.serial, each.serial, self.idNext, requestDest)), self.get_neighbor_latency(each.serial))

				# all the broadcast packet's id should be same, so after send all the packet, we increase the number
				self.idNext += 1

			return Node.PACKET_HAS_PROCESSED


		# process Route Response packet
		res = Packet.test_RR_packet(packet)
		if res is not None:
			if self.update_route(packet):
				latency = res['latency']
				dest = res['dest']
				nextPort = self.serial

				# broadcast the update of the route
				for each in self.neighbors:
					each.receive(Frame(self.serial, each.serial,
									   Packet.generate_RR_packet(self.serial,
																each.serial,
																dest,
																self.idNext,
																latency + self.table.get_latency(each.serial),
																nextPort,
																None)), self.get_neighbor_latency(each.serial))

				self.idNext += 1

			return Node.PACKET_HAS_PROCESSED

		####################################################################
		# NOT THE CONTROL PACKET, LEAVE IT TO THE NEXT LAYER
		####################################################################

		if packet.dest == self.serial:
			return Node.PACKET_IN_PAYLOAD

		else:
			return Node.PACKET_FORWARD

	def process_packet_marking(self, packet):
		# simplify version, designed by p1usj4de
		if not packet.test_mark_id():
			packet.mark_id(self.serial)
		elif not packet.test_preceding():
			packet.mark_preceding(self.serial)
		else:
			pass

		return
		# all the code has been deprecated
		if self.serial == SINK_NODE_ID:
			return # only intermediate node do the packet marking procedure

		if not (packet.dest == SINK_NODE_ID and self.table.item_exist(SINK_NODE_ID)):
			return

		if packet.has_marked():
			return # do nothing

		if not self.cache.itemExist(packet.source):
			# mark packet with its own ID
			packet.mark_id(self.serial)

			# fill in the MAC field
			packet.mark_MAC(None)

			# create entry with source ID, sequence and hopcount in packet
			self.cache.update(packet.source, sequence=packet.id, hopcount=packet.hopcount)

			#print "packet not marked"
			#print packet.debug_str()

		elif self.cache.itemExist(packet.source) and self.cache.get_sequence(packet.source) == packet.id - 1:
			if self.cache.get_hopcount(packet.source) == packet.hopcount:
				# update cache entry with new sequence number
				self.cache.update(packet.source, sequence=packet.id)

				# fill in the preceding node ID
				packet.mark_preceding(self.serial)

				# fill in the MAC field
				packet.mark_MAC(None)

				#print "cache existed, sequence continue and hopcount equal"
				#print packet.debug_str()

			else:
				# fill packet.hopcount field with cache.hopcount
				packet.hopcount = self.cache.get_hopcount(packet.source)

				# mark packet with alert message
				packet.mark_alert()

				# fill in the preceding node ID with its own Id
				packet.mark_preceding(self.serial)

				# fill in the MAC field
				packet.mark_MAC(None)

				#print "cache existed and sequence continue but hopcount not equal "
				#print packet.debug_str()

		elif self.cache.itemExist(packet.source) and not (self.cache.get_sequence(packet.source) == packet.id - 1):
			# mark packet with its own ID
			packet.mark_id(self.serial)

			# fill in the MAC field
			packet.mark_MAC(None)

			# update cache entry with new sequence number and hopcount
			self.cache.update(packet.source, sequence=packet.id, hopcount=packet.hopcount)

			#print "cache existed but sequence not continue"
			#print packet.debug_str()

	def process_wormhole_detection(self):
		originAverageHopcount = self.backupCache.get_average_hopcount()
		newAverageHopcount = self.cache.get_average_hopcount()

		originAverageDelay = self.backupCache.get_average_delay()
		newAverageDelay = self.cache.get_average_delay()

		frequentAppearedNodes = self.topology.most_frequent_nodes()
		mostAbsorbedTrafficNodes = self.topology.each_node_absorbed_traffic()

		newAddedNode = Topology.difference(self.backupTopology, self.topology)
		clue = 0

		def get_rate_changed(origin, new):
			return "%4.2f" % (float(new-origin) / float(origin))

		print "--------------------------------------------------------------------"
		print "| [!] WORMHOLE DETECTION PHASE!"
		print "| [!] The new added node is %d" % newAddedNode
		print "|"
		print "| [!] The last time stabled average hopcount is %f." % originAverageHopcount
		print "| [!] The latest stabled average hopcount is %f." % newAverageHopcount
		print "| [!] The rate of change is " + get_rate_changed(originAverageHopcount, newAverageHopcount)
		print "|"
		print "| [!] The last time stabled average time delay is %f." % originAverageDelay
		print "| [!] The latest stabled average time delay is %f." % newAverageDelay
		print "| [!] The rate of change is " + get_rate_changed(originAverageDelay, newAverageDelay)
		print "|"
		print "| [!] The last time most frequent nodes are : " + str(self.backupTopology.most_frequent_nodes())
		print "| [!] The latest most frequent nodes are : " + str(frequentAppearedNodes)
		print "|"
		print "| [!] The last time traffic frequences are : " + str(self.backupTopology.each_node_absorbed_traffic())
		print "| [!] The latest time traffic frequences are : " + str(mostAbsorbedTrafficNodes)
		print "--------------------------------------------------------------------"
		print "| [!] Result:"
		if str(newAddedNode) in [res[0] for res in frequentAppearedNodes]:
			clue += 1
		if newAverageHopcount < (originAverageHopcount * 0.8):
			clue += 1
		if newAverageDelay < (originAverageDelay * 0.8):
			clue += 1

		location = self.topology.fix_position(newAddedNode)
		print "| [!]     The new added node's locatino is between %d and %d" % (location[0], location[1])

		if clue >= 2:
			print "| [!]     The new added node is a wormhole, Exit program!"
			print "--------------------------------------------------------------------"
			sys.exit(0)
		else:
			print "| [!]     Network changed, nothing matter, continue executing!"
			print "--------------------------------------------------------------------"


		self.cache.backup(self.backupCache)
		self.topology.backup(self.backupTopology)

	def process_packet_parsing(self, packet):
		# simplify version, designed by p1usj4de
		if not self.serial == SINK_NODE_ID:
			return

		# update the hopcount cache
		self.cache.update(packet.source, hopcount=packet.hopcount, delay=packet.delay)

		# determine what the sink node should do based on the packet's topology information
		if self.networkStatus == Node.NETWORK_INIT:
			self.topology.store(packet.source, packet.markId)
			self.topology.store(packet.markId, packet.precedingId)

			if self.topology.get_path_number() == self.intermediateNodesNum:
				self.topology.backup(self.backupTopology)
				self.cache.backup(self.backupCache)

				self.networkStatus = Node.NETWORK_STABLED

				if not self.networkStabledPromptDisplayOnlyOnce:
					print "--------------------------------------------------------------------"
					print "| [!] Network init finished! All the nodes have stabled."
					print "--------------------------------------------------------------------"
					self.networkStabledPromptDisplayOnlyOnce = True

		if self.networkStatus == Node.NETWORK_STABLED:
			if self.topology.item_exist(packet.source, packet.markId) and packet.precedingId is None:
				pass # do nothing
			elif self.topology.item_exist(packet.source, packet.markId) and self.topology.item_exist(packet.markId, packet.precedingId):
				pass # do nothing
			else:
				self.networkStatus = Node.NETWORK_CHANGED

				if not self.networkChangedPromptDisplayOnlyOnce:
					print "--------------------------------------------------------------------"
					print "| [!] Detected network changed! "
					print "--------------------------------------------------------------------"
					self.topology.clear()
					self.networkChangedPromptDisplayOnlyOnce = True

		if self.networkStatus == Node.NETWORK_CHANGED:
			self.topology.store(packet.source, packet.markId)
			self.topology.store(packet.markId, packet.precedingId)

			if self.topology.get_path_number() > self.intermediateNodesNum:
				self.networkStatus = Node.NETWORK_RESTABLED

				if not self.networkRestabledPromptDisplayOnlyOnce:
					print "--------------------------------------------------------------------"
					print "| [!] Network Restabled!"
					print "--------------------------------------------------------------------"
					self.networkRestabledPromptDisplayOnlyOnce = True

		if self.networkStatus == Node.NETWORK_RESTABLED:
			self.process_wormhole_detection()
			self.networkRestabledPromptDisplayOnlyOnce = False
			self.networkChangedPromptDisplayOnlyOnce = False
			self.networkStatus = Node.NETWORK_STABLED

		return
		# all the code has been deprecated
		if not self.serial == SINK_NODE_ID:
			return # only sink node do the packet parsing procedure

		print packet.debug_str()

		source = packet.source
		hopcount = packet.hopcount
		sequence = packet.id
		markId = packet.get_mark_id()

		if not self.topology.has_path(source):
			self.topology.new_path(source, hopcount)

		else:
			if not packet.has_marked():
				self.cache.update(source, sequence=sequence)
				print "update cache for %d sequence %d" % (source, sequence)
			else:
				if not packet.test_MAC():
					# generate attacking report on path packet.source
					print "PACKET INTEGRITY VERIFY FAILED, ALERT ATTACK"

				else:
					if packet.test_alert():
						# generate attacking report at location packet.hopcount-1 of that path
						print "**********************************************************************"
						print "* PACKET ALERT MESSAGE RECEIVED!"
						print "* THE ATTACKING POINT MAY BE : " + self.topology.get_node(source, hopcount-1)
						print "**********************************************************************"

					else:
						d = sequence - self.cache.get_sequence(source)
						if d<=1:
							if self.topology.get_node(source, hopcount-1) != packet.get_preceding():
								# generate attacking report at location path[hopcount-1] of that path
								print "**********************************************************************"
								print "* PACKET ALERT MESSAGE RECEIVED!"
								print "* THE ATTACKING POINT MAY BE : " + self.topology.get_node(source, hopcount - 1)
								print "**********************************************************************"

							else:
								self.topology.update_path(source, hopcount, markId)
								self.topology.clear_path(source, hopcount+1)
								print "**********************************************************************"
								print "* ROUTE SWITCH REPORT!"
								print "**********************************************************************"

						else:
							# generate packet loss report

							if self.topology.get_node(source, hopcount) != markId:
								self.topology.clear_path(source, hopcount-d+1)
								self.topology.update_path(source, hopcount, markId)
								print "**********************************************************************"
								print "* ROUTE SWITCH REPORT!"
								print "**********************************************************************"

	# -------------------------------------------------------------------
	# APPLICATION LAYER
	# NOTES: ALL THE PARAMETERS WITH A DEFAULT VALUE SHOULD NOT BE
	# GOT BY THIS LAYER, THAT'S JUST FOR DEBUG USAGE
	# -------------------------------------------------------------------
	def process_payload(self, payload, frame=None, packet=None):
		if self.BEFORE_PAYLOAD(payload) == Node.DROP:
			return

		if not self.serial == SINK_NODE_ID:
			return

		# sink node can something here, like process the data
		print "[*] SINK NODE got one packet :"
		print packet
		print packet.delay


	def receive(self, frame, timeDelay):
		if self.BEFORE_RECEIVE(frame) == Node.DROP:
			return

		if frame.packet is not None:
			frame.packet.decrease_ttl()

		# this function should be put into the process_packet()
		# but we put here to enhance the node's process ability
		if frame.packet is not None and not frame.packet.alive():
			return

		# increase the hop-count
		frame.packet.hopcount += 1
		# increase the time delay
		frame.packet.delay += timeDelay
		# add the frame into Frame Buffer
		self.buffer.append(frame)

	# -------------------------------------------------------------------
	# NETFILTER FUNCTIONS
	# NOTES: THESE FUNCTION IS A SIMULATOR FOR NETFILTER+IPTABLE LIKE
	# THE LINUX SYSTEM, AIM TO EASY TO DEBUG AND WRITER WORMHOLE METHOD
	# -------------------------------------------------------------------
	def BEFORE_RECEIVE(self, frame):
		return Node.CONTINUE

	def BEFORE_PACKET(self, packet):
		return Node.CONTINUE

	def BEFORE_FRAME(self, frame):
		return Node.CONTINUE

	def BEFORE_PAYLOAD(self, payload):
		return Node.CONTINUE

	def send_neighbor_packet(self, target, packet):
		self.wantSpeak = True

		basicCount = 0 # the yes reply counter
		basicTotal = 0 # the number which yes number should reached

		# send speaking beacon
		for x in range(len(self.neighbors)):
			beaconFrame = Frame.generate_speaking_beacon(self.serial, self.neighbors[x].serial, self.carrierBasic)
			basicTotal = self.carrierBasic
			self.carrierBasic += 1
			self.neighbors[x].receive(beaconFrame, self.latencies[x])

		startTime = time.time()

		# wait for speaking beacon's reply
		while True:
			for x in range(len(self.neighbors)):
				if len(self.buffer) == 0:
					time.sleep(0.2)
				if len(self.buffer) == 0:
					continue

				frm = self.buffer.popleft()
				res = Frame.test_speaking_reply(frm)

				if res is None:
					# the frame is not the speaking beacon's reply, put it back to the buffer
					self.buffer.append(frm)
				elif res:
					# the reply is yes, count the value
					basicCount += frm.ack
					if basicCount == basicTotal:
						# all the reply are yes, then send the packet
						target.receive(Frame(self.serial, target.serial, packet), self.get_neighbor_latency(target.serial))
						self.idNext += 1
						self.wantSpeak = False
						return True
				else:
					self.wantSpeak = False
					return False

				# time is up, no longer wait for the reply
				if time.time() - startTime >= 3:
					self.wantSpeak = False
					return False

	def send_neighbor_payload(self, target, payload):
		self.send_neighbor_packet(target, Packet(self.serial, target.serial, payload, self.idNext))

	def send_packet(self, targetId, packet):
		if self.table.item_exist(targetId):
			nextPort = self.table.get_next(targetId)
			nextPort = self.get_neighbor(nextPort)
			nextPort.receive(Frame(self.serial, nextPort.serial, packet), self.table.get_latency(targetId))
			self.idNext += 1

		return

		# this is the origin code, now deprecated
		if self.table.item_exist(targetId):
			nextPort = self.table.get_next(targetId)
			self.send_neighbor_packet(self.get_neighbor(nextPort), packet)

	def send_payload(self, targetId, payload):
		if self.table.item_exist(targetId):
			nextPort = self.table.get_next(targetId)
			nextPort = self.get_neighbor(nextPort)
			nextPort.receive(Frame(self.serial, nextPort.serial, Packet(self.serial, targetId, payload, self.idNext)), self.table.get_latency(targetId))
			self.idNext += 1
		return

		# this is the origin code, now deprecated
		if self.table.item_exist(targetId):
			nextPort = self.table.get_next(targetId)
			self.send_neighbor_packet(self.get_neighbor(nextPort), Packet(self.serial, targetId, payload, self.idNext))
		else:
			# send a query
			pass

	def update_route(self, packet):
		res = Packet.test_RR_packet(packet)
		if res is None:
			return False

		dest = res['dest']
		nextPort = res['next']
		latency = res['latency']

		return self.table.update(dest, nextPort, latency)

	def init_route(self):
		# add myself port
		self.table.update(self.serial, self.serial, 0.0)

		# add all the direct-connect port
		if not len(self.neighbors) == len(self.latencies):
			exit("Exception: %d's neighbors number is not equal with the latencies number!" % self.serial)

		for each in range(len(self.neighbors)):
			eachSerial = self.neighbors[each].serial
			eachLatency = self.latencies[each]

			self.table.update(eachSerial, eachSerial, eachLatency)

		# send a packet to query the sink node's route path
		if not self.table.item_exist(SINK_NODE_ID):
			self.broadcast_query(SINK_NODE_ID)

	def broadcast_packet(self, packet):
		for each in self.neighbors:
			self.send_neighbor_packet(each, packet)

	def broadcast_query(self, queryDest):
		for each in self.neighbors:
			each.receive(Frame(self.serial, each.serial, Packet.generate_RQ_packet(self.serial, each.serial, self.idNext, queryDest)), self.get_neighbor_latency(each.serial))
		self.idNext += 1

		return

		# this is the origin code, now deprecated
		for each in self.neighbors:
			self.send_neighbor_packet(each, Packet.generate_RQ_packet(self.serial, each.serial, self.idNext, queryDest))
		self.idNext += 1

	def forward(self, packet):
		if self.table.item_exist(packet.dest):
			nextPort = self.get_neighbor(self.table.get_next(packet.dest))
			if nextPort is None:
				# send a query for the destination and discard the packet
				self.broadcast_query(packet.dest)
				return False
			else:
				nextPort.receive(Frame(self.serial, nextPort.serial, packet), self.table.get_latency(packet.dest))
				return True

	def run(self):
		# use interval to create some delay
		clockStart = time.time()

		self.init_route()

		while True:
			frm = None
			ret = None
			pkt = None

			if len(self.buffer)!=0:
				frm = self.buffer.popleft()
				ret = self.process_frame(frm)

			if ret == Node.FRAME_IN_PACKET:
				pkt = frm.packet
				ret = self.process_packet(pkt)
			else:
				ret = None

			if ret == Node.PACKET_IN_PAYLOAD:
				self.process_payload(pkt.payload, frame=frm, packet=pkt)
			elif ret == Node.PACKET_FORWARD:
				self.forward(pkt)
			elif ret == Node.PACKET_HAS_PROCESSED:
				pass

			if time.time() - clockStart >= self.interval:
				# sink node is not the sensor node
				if self.sendMessageFlag and not self.serial == SINK_NODE_ID:
					self.send_payload(SINK_NODE_ID, 'Nuts')

				clockStart = time.time()


class Wormhole(Node):
	def __init__(self, serial, oneEnd, anotherEnd, linkConsume=0.01):
		Node.__init__(self, serial, 100000,100000)

		self.oneEnd = oneEnd
		self.anotherEnd = anotherEnd
		self.linkConsume = linkConsume
		self.sendMessageFlag = False

		print "--------------------------------------------------------------------"
		print "| [!] The wormhole inserted between %d and %d" % (self.oneEnd.serial, self.anotherEnd.serial)
		print "--------------------------------------------------------------------"

	def BEFORE_PACKET(self, packet):
		pass
		#print "[***] Wormhole got packet."
		#print packet

	def init_route(self):
		# add myself port
		self.table.update(self.serial, self.serial, 0.0)

		# modify my route table
		self.table.update(self.oneEnd.serial, self.oneEnd.serial, self.linkConsume)
		self.table.update(self.anotherEnd.serial, self.anotherEnd.serial, self.linkConsume)

		# modify the ends's route table
		self.oneEnd.table.update(self.serial, self.serial, self.linkConsume)
		self.anotherEnd.table.update(self.serial, self.serial, self.linkConsume)

		# add myself to two ends's neighbors
		self.oneEnd.neighbors.append(self)
		self.anotherEnd.neighbors.append(self)

		self.oneEnd.latencies.append(self.linkConsume)
		self.anotherEnd.latencies.append(self.linkConsume)

		# add two ends to my neighbors
		self.neighbors.append(self.oneEnd)
		self.neighbors.append(self.anotherEnd)

		self.latencies.append(self.linkConsume)
		self.latencies.append(self.linkConsume)

		# send packets to modify the route path
		#self.oneEnd.receive(Frame(self.serial, self.oneEnd.serial, Packet.generate_RR_packet(self.serial, self.oneEnd.serial, self.oneEnd.serial, self.idNext, self.linkConsume, self.serial, 0)))
		#self.anotherEnd.receive(Frame(self.serial, self.anotherEnd.serial, Packet.generate_RR_packet(self.serial, self.anotherEnd.serial, self.anotherEnd.serial, self.idNext, self.linkConsume, self.serial, 0)))

		# send a packet to query the sink node's route path
		if not self.table.item_exist(SINK_NODE_ID):
			self.broadcast_query(SINK_NODE_ID)
		else:
			notSinkNode = self.oneEnd if self.oneEnd.serial != SINK_NODE_ID else self.anotherEnd
			notSinkNode.receive(Frame(self.serial, notSinkNode.serial, Packet.generate_RR_packet(self.serial, notSinkNode.serial, SINK_NODE_ID, self.idNext, self.linkConsume, self.serial, 0)), self.get_neighbor_latency(notSinkNode.serial))
			self.idNext += 1