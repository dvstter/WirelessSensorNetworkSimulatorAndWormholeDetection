"""
    File Name: routetbl.py
    File Creator: p1usj4de
    File Description: defines the RouteTable class
"""

class RouteTable:
    tableTitleForm = "%s[*] Route Table for Node %s\n" \
                "%s----------------------------\n" \
                "%s|   Id| Dest| Next| Latency|\n" \
                "%s----------------------------\n"
    tableItemForm = "%s|%5d|%5d|%5d|%8.2f|\n" \
                    "%s----------------------------\n"
    def __init__(self, nodeSerial=None):
        self.table = {}
        self.nodeSerial = nodeSerial

        self.indent = 0

    def update(self, dest, nextPort, latency):
        latency = float(latency)
        dest = str(dest)
        if self.table.has_key(dest) and latency < self.table[dest][1]:
            self.table[dest] = (nextPort, latency)
            return True
        elif not self.table.has_key(dest):
            self.table[dest] = (nextPort, latency)
            return True
        else:
            return False

    def __str__(self, indent=0):
        result = RouteTable.tableTitleForm % (" "*indent, str(self.nodeSerial), " "*indent, " "*indent, " "*indent)
        idx = 0
        for key in self.table.keys():
            nextPort, latency = self.table[key]
            result += RouteTable.tableItemForm % (" "*indent, idx, int(key), int(nextPort), latency, " "*indent)
            idx += 1

        return result

    def str_with_indent(self, indent):
        return self.__str__(indent)

    def item_exist(self, dest):
        return True if self.table.has_key(str(dest)) else False

    def get_next(self, dest):
        dest = str(dest)
        return self.table[dest][0] if self.table.has_key(dest) else None

    def get_latency(self, dest):
        dest = str(dest)
        return self.table[dest][1] if self.table.has_key(dest) else None

        