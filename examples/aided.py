import logging

from fsort import Sorter, run

LOG = logging.getLogger(__name__)

class Dixon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dixon")

    def run(self):
        self.add(seriesdescription="mdixon", protocolname="bh", nvols=6)
        if self.have_files():
            LOG.info("Found 6-volume mDIXON")
            self.select_earliest()
            self.save("water", vol=0)
            self.save("ip", vol=1)
            self.save("op", vol=2)
            self.save("fat", vol=3)
            self.save("fat_fraction", vol=4)
            self.save("t2star", vol=5)
            return

        self.add(seriesdescription="mdixon", protocolname="bh", nvols=4)
        if self.have_files():
            LOG.info("Found 4-volume mDIXON")
            self.select_earliest()
            if self.count(imagetype="ff"):
                # Special case, different order
                self.save("t2star", vol=0)
                self.save("water", vol=1)
                self.save("fat", vol=2)
                self.save("fat_fraction", vol=3)
            else:
                self.save("water", vol=0)
                self.save("fat", vol=1)
                self.save("fat_fraction", vol=2)
                self.save("t2star", vol=3)
            return

        self.add(seriesdescription="mdixon", protocolname="bh", nvols=3)
        if self.have_files():
            LOG.info("Found 3-volume mDIXON")
            self.select_earliest()
            self.save("water", vol=0)
            self.save("fat", vol=1)
            self.save("fat_fraction", vol=2)
            self.clear_selection()
            self.add(seriesdescription="mdixon", protocolname="bh", nvols=1)
            if self.have_files():
                LOG.info("Added 1-volume t2star mDIXON")
                self.select_earliest()
                self.save("t2star")
            return

        LOG.warn("Couldn't find mDIXON data with 3, 4 or 6 volumes")

SORTERS = [
    Dixon(),
]

if __name__ == "__main__":
    run(__file__)
