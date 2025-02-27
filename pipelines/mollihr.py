import logging

from fsort import Sorter, run, sorters

from afirm import B0

LOG = logging.getLogger(__name__)

class MDixon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dixon")

    def run(self):
        self.add(seriesdescription="mdixon", nvols=3)
        if self.have_files():
            self.select_latest()
            self.save("water", vol=0)
            self.save("fat", vol=1)
            self.save("fat_fraction", vol=2)
        self.clear_selection()
        self.add(seriesdescription="mdixon", nvols=1)
        if self.have_files():
            self.select_latest()
            self.save("t2star", vol=0)

class Molli(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli")

    def _remove_not_7_tis(self):
        ignore = []
        for f in self.selected:
            tis = [t for t in f.inversiontimedelay if t > 0.1]
            if len(tis) != 7:
                LOG.warn(f"Ignoring {f.fname}: has wrong number of TIs: {tis}")
                ignore.append(f.seriesnumber)
        for seriesnumber in ignore:
            self.remove(seriesnumber=seriesnumber)

    def run(self):
        self.add(seriesdescription="cor_t1_molli", nvols=10)
        if self.have_files():
            self._remove_not_7_tis()
            self.save("t1_map", vol=8, sort="SeriesNumber")
            self.save("t1_conf", vol=9, sort="SeriesNumber")
        else:
            self.add(seriesdescription="cor_t1_molli", nvols=2)
            if self.have_files():
                self._remove_not_7_tis()
                self.scale(attribute="PhilipsRWVSlope", inverse=True)
                self.save("t1_map", vol=0, sort="SeriesNumber")
                self.save("t1_conf", vol=1, sort="SeriesNumber")
            else:
                LOG.info(" - No MOLLI data found")

class MolliRaw(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli_raw")

    def run(self):
        self.add(seriesdescription="cor_t1_molli", nvols=7)
        if self.have_files():
            self.save("molli_raw", sort="SeriesNumber")

SORTERS = [
    MDixon(),
    Molli(),
    MolliRaw(),
    sorters.B0TwoEchos(),
    sorters.B1(seriesdescription="cor_b1map"),
]

if __name__ == "__main__":
    run(__file__)
