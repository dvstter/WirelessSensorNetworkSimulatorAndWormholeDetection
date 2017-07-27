"""
    File Name: ncache.py
    File Creator: p1usj4de
    File Description: defines the NodeCache class, which represent the node's cache for wormhole detection
"""

class NodeCache:
    tableTitleForm = "%s[*] Cache for Node %d\n" \
                     "%s-------------------------------\n" \
                     "%s|   Id|  Src|  Seq|  Hop|Delay|\n" \
                     "%s-------------------------------\n"

    tableItemForm = "%s|%5d|%5s|%5d|%5d|%5.2f|\n" \
                    "%s-------------------------------\n"

    def __init__(self, nodeId):
        self.serial = nodeId

        self.cache = {}

    def __str__(self, indent=0):
        result = NodeCache.tableTitleForm % (" "*indent, self.serial, " "*indent, " "*indent, " "*indent)
        idx = 0
        for item in self.cache.keys():
            result += NodeCache.tableItemForm % (" "*indent, idx, item, self.cache[item][0], self.cache[item][1], self.cache[item][2], " "*indent)
            idx+=1

        return result

    def itemExist(self, sourceId):
        return str(sourceId) in self.cache.keys()

    def update(self, sourceId, sequence=None, hopcount=None, delay=None):
        # if entry not existed, create one
        if not self.itemExist(sourceId):
            self.cache[str(sourceId)] = [0, 0, 0.0]

        if sequence is not None:
            self.cache[str(sourceId)][0] = sequence
        if hopcount is not None:
            self.cache[str(sourceId)][1] = hopcount
        if delay is not None:
            self.cache[str(sourceId)][2] = float(delay)

    def backup(self, nodeCache):
        for each in self.cache.keys():
            nodeCache.update(each, sequence=self.get_sequence(each), hopcount=self.get_hopcount(each), delay=self.get_delay(each))

    def get_sequence(self, sourceId):
        if self.itemExist(sourceId):
            return self.cache[str(sourceId)][0]
        else:
            return None

    def get_hopcount(self, sourceId):
        if self.itemExist(sourceId):
            return self.cache[str(sourceId)][1]
        else:
            return None

    def get_delay(self, sourceId):
        if self.itemExist(sourceId):
            return float(self.cache[str(sourceId)][2])
        else:
            return None

    def get_average_hopcount(self):
        length = len(self.cache.keys())
        total = 0
        for each in self.cache.keys():
            total += self.get_hopcount(each)

        return float(total) / float(length)

    def get_average_delay(self):
        length = len(self.cache.keys())
        total = 0.0
        for each in self.cache.keys():
            total += self.get_delay(each)

        return total / float(length)

    def set_sequence(self, sourceId, sequence):
        self.update(sourceId, sequence=sequence)

    def set_hopcount(self, sourceId, hopcount):
        self.update(sourceId, hopcount=hopcount)

    def set_delay(self, sourceId, delay):
        self.update(sourceId, delay=delay)
