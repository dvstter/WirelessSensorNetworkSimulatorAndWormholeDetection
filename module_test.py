from topo import *

if __name__ == '__main__':
    test = Topology()

    test.new_path(1, 5)
    print test.topo
    test.update_path(1, 5, 1)
    print test.topo
    test.update_path(1, 6, 2)
    print test.topo
    test.update_path(1, 10, 3)
    print test.topo