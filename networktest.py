"""
    File Name: network.py
    File Creator: p1usj4de
    File Description: this file is dedicated to the large network create and control
"""

import random
import math
import threading

from node import *

TEST_FILE = "./NetworkFiles/medium_network_test.txt"

class WSNNetworkManager:
    def __init__(self):
        self.nodes = []

        # change network configuration here
        self.load_from_file(TEST_FILE)

    def load_from_file(self, filename):
        handler = file(filename, "r")

        idx = 0
        for eachLine in handler.xreadlines():
            eachLine = eachLine.strip()
            if eachLine == "":
                break

            infos = eachLine.split(' ')
            self.nodes.append(Node(idx, int(infos[0]), int(infos[1])))
            idx += 1

        handler.close()

    def create_test_nodes(self, nodesNum=10):
        self.nodes = [Node(0, 0, 0), Node(1, 5, 5), Node(2, 10, 12), Node(3, 10, 10), Node(4, 12, 17), Node(5, 15, 20), Node(6, 20, 22), Node(7, 25, 27), Node(8, 25, 20), Node(9, 30, 40)]

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
        wormhole = Wormhole(1000, self.nodes[0], self.nodes[62])
        thread = threading.Thread(target=Wormhole.run, args=(wormhole,))
        thread.setDaemon(True)
        thread.start()

        # after any input, shutdown the game and print the new topology with the most frequently appear nodes
        raw_input()

        print "Exit!"

        return