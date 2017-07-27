"""
    File Name: network.py
    File Creator: p1usj4de
    File Description: this file is dedicated to the large network create and control
"""

from random import randint
from math import sqrt
import threading

from node import *

RANDOM_NODES_NUMBER = 100

class WSNNetworkManager:
    def __init__(self):
        self.nodes = []

        # change network configuration here
        self.create_random_nodes()

    def create_random_nodes(self):
        distance = int(sqrt(NEIGHBOR_DISTANCE_SQUARE)/2)
        sqrt(RANDOM_NODES_NUMBER)

    def run(self):
        for x in self.nodes:
            x.neighbors_find(self.nodes)

        threads = [threading.Thread(target=Node.run, args=(each,)) for each in self.nodes]
        for x in threads:
            x.setDaemon(True)
            x.start()

        # after any input insert a wormhole
        raw_input()

        # insert the wormhole node here
        wormhole = Wormhole(1000, self.nodes[randint(0, RANDOM_NODES_NUMBER-1)], self.nodes[randint(0, RANDOM_NODES_NUMBER-1)])
        thread = threading.Thread(target=Wormhole.run, args=(wormhole,))
        thread.setDaemon(True)
        thread.start()

        # after any input, shutdown the game and print the new topology with the most frequently appear nodes
        raw_input()

        print "Exit!"

        return
