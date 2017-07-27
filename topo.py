"""
	File Name: topo.py
	File Creator: p1usj4de
	File Description: defines the class which sink node use to manage the network's topology
"""

from node import *

# simplify version designed by p1usj4de
class Topology:
    def __init__(self):
        self.precedings = {}

    def __str__(self):
        result = "Original Preceding Data : \n"
        new_line = 0
        for each in self.precedings.keys():
            result += "%d->%d " % (int(each), self.precedings[each])
            new_line += 1
            if new_line == 5:
                new_line = 0
                result += '\n'

        if result[-1] != '\n':
            result+='\n'

        result += "Path : \n"
        for each in self.precedings.keys():
            path = self.get_path(int(each))
            result += str(path) + '\n'

        return result

    def get_path_number(self):
        return len(self.precedings)

    def get_origin_data(self):
        return self.precedings

    def get_all_paths_data(self):
        result = []
        for each in self.precedings.keys():
            path = self.get_path(int(each))
            result.append(path)

        return result

    def backup(self, topology):
        for each in self.precedings.keys():
            topology.store(each, self.precedings[each])

    def clear(self):
        self.precedings.clear()

    def item_exist(self, source, preceding):
        if preceding is None:
            return False

        source = str(source)
        preceding = int(preceding)
        if source in self.precedings.keys() and self.precedings[source] == preceding:
            return True
        else:
            return False

    def store(self, source, preceding):
        if preceding is not None:
            self.precedings[str(source)] = int(preceding)

    def get_path(self, source):
        result = [int(source)] # will return a array with all int
        source = str(source)

        while source in self.precedings.keys():
            preceding = self.precedings[source]
            result.insert(0, preceding)
            source = str(preceding)
            if preceding == 0: # 0 must be the sink node id
                break

        return result

    def most_frequent_nodes(self):
        tmp = {}
        for each in self.precedings.keys():
            path = self.get_path(each)
            for eachNode in path:
                if str(eachNode) not in tmp.keys():
                    tmp[str(eachNode)] = 1
                else:
                    tmp[str(eachNode)] += 1

        return sorted(tmp.items(), key=lambda e:e[1], reverse=True)[:5]

    def target_absorbed_traffic(self, nodeSerial):
        paths = self.get_all_paths_data()
        result = {}
        length = len(self.precedings.keys())
        for each in self.precedings.keys():
            for eachPath in paths:
                if int(each) in eachPath:
                    if each not in result.keys():
                        result[each] = 1
                    else:
                        result[each] += 1

        for each in result.keys():
            result[each] = "%4.2f" % (float(result[each]) / float(length))

        tmpResult = sorted(result.items(), key=lambda e: e[1], reverse=True)
        for each in tmpResult:
            if nodeSerial == int(each[0]):
                return each[1]

    def each_node_absorbed_traffic(self):
        paths = self.get_all_paths_data()
        result = {}
        length = len(self.precedings.keys())
        for each in self.precedings.keys():
            for eachPath in paths:
                if int(each) in eachPath:
                    if each not in result.keys():
                        result[each] = 1
                    else:
                        result[each] += 1

        for each in result.keys():
            result[each] = "%4.2f%%" % (float(result[each]) / float(length))

        return sorted(result.items(), key=lambda e:e[1], reverse=True)[:5]

    def fix_position(self, serial):
        end = self.precedings[str(serial)]
        another = None
        for each in self.precedings.keys():
            if self.precedings[each] == serial:
                another = each
        if another is not None and end is not None:
            return int(end), int(another)
        else:
            return None

    @staticmethod
    def difference(topology1, topology2):
        k1 = set(topology1.precedings.keys())
        k2 = set(topology2.precedings.keys())
        if len(k1) > len(k2):
            return int(list(k1 - k2)[0])
        elif len(k1) < len(k2):
            return int(list(k2 - k1)[0])
        else:
            return None


# old version of implementation
"""
class Topology:
    def __init__(self):
        self.topo = {}

    def new_path(self, sourceId, length):
        if not self.has_path(sourceId):
            self.topo[str(sourceId)] = [None for _ in range(length + 1)]
            return True

        return False

    def update_path(self, sourceId, hopcount, targetId):
        if self.has_path(str(sourceId)):
            path = self.topo[str(sourceId)]
            length = len(path)

            # test the path's length is enough or not
            if length>hopcount:
                path[hopcount] = targetId
            else:
                # not enough, extend it
                [path.append(None) for _ in range(hopcount - length + 1)]
                path[hopcount] = targetId
            return True

        return False

    def clear_path(self, sourceId, start, end=None):
        path = self.topo[str(sourceId)]
        length = end if end is not None else len(path)

        if self.has_path(sourceId):
            for x in range(start, length):
                path[x] = None

            return True

        return False

    def get_node(self, sourceId, hopcount):
        return self.topo[str(sourceId)][hopcount]

    def has_path(self, sourceId):
        return str(sourceId) in self.topo.keys()
"""