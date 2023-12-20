import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class Dixon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dixon")

    def run(self):
        self.add(seriesdescription="mdixon", nvols=6)
        self.select_latest()
        self.save("water", vol=0)
        self.save("ip", vol=1)
        self.save("op", vol=2)
        self.save("fat", vol=3)
        self.save("fat_fraction", vol=4)
        self.save("t2star", vol=5)

SORTERS = [
    Dixon(),
]
