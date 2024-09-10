import logging

from fsort import Sorter, run

LOG = logging.getLogger(__name__)

from afirm import B0

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

class EThrive(Sorter):
    def __init__(self):
        Sorter.__init__(self, "ethrive")

    def run(self):
        self.add(seriesdescription="thrive")
        self.select_latest()
        self.save("ethrive")

class T2w(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t2w")

    def run(self):
        self.add(seriesdescription="t2w")
        self.select_latest()
        self.save("t2w")

class MolliKidney(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli_kidney")

    def run(self):
        self.add(seriesdescription="kidney_cor_t1_molli", nvols=10)
        if self.have_files():
            self.select_latest()
            self.save("t1_map", vol=8)
            self.save("t1_conf", vol=9)
        else:
            self.add(seriesdescription="kidney_cor_t1_molli", nvols=2)
            self.select_latest()
            self.scale(attribute="PhilipsRWVSlope", inverse=True)
            self.save("t1_map", vol=0)
            self.save("t1_conf", vol=1)

class AxB1(Sorter):
    """
    B1 mapping data
    """
    def __init__(self):
        Sorter.__init__(self, "b1_ax")

    def run_philips(self):
        self.add(seriesdescription="ax_b1map", imagetype="b1", nvols=1)
        self.remove(imagetype="phase")
        if self.have_files():
            self.select_latest()
            self.save("b1")

class AxB0(Sorter):
    """
    B0 mapping data
    """
    def __init__(self):
        Sorter.__init__(self, "b0_ax")

    def run_philips(self):
        self.add(seriesdescription="ax_b0map", imagetype="b0", nvols=1)
        if self.have_files():
            self.select_latest()
            self.save("b0")

class CorB1(Sorter):
    """
    B1 mapping data
    """
    def __init__(self):
        Sorter.__init__(self, "b1_cor")

    def run_philips(self):
        self.add(seriesdescription="cor_b1map", imagetype="b1", nvols=1)
        self.remove(imagetype="phase")
        if self.have_files():
            self.select_latest()
            self.save("b1")

class CorB0(Sorter):
    """
    B0 mapping data
    """
    def __init__(self):
        Sorter.__init__(self, "b0_cor")

    def run_philips(self):
        self.add(seriesdescription="cor_b0map", imagetype="b0", nvols=1)
        if self.have_files():
            self.select_latest()
            self.save("b0")

SORTERS = [
    MDixon(),
    EThrive(),
    T2w(),
    MolliKidney(),
    AxB0(),
    AxB1(),
    CorB0(),
    CorB1(),
]

if __name__ == "__main__":
    run(__file__)
