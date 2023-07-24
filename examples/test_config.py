from fsort import Sorter

class T1map(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t1map")

    def run(self):
        pass

class T2star(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t2star")

    def run(self):
        pass

SORTERS = [
    T1map(),
    T2star(),
]
