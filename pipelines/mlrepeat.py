import logging

from fsort import Sorter, run, sorters

LOG = logging.getLogger(__name__)

class T1Molli(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t1_molli")

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
    sorters.MDixon(name="dixon", seriesdesc_inc="mdixon"),
    sorters.SeriesDesc(name="ethrive", seriesdesc=["ethrive", "e_thrive", "thrive"]),
    sorters.SeriesDesc("t2w"),
    T1Molli(),
    AxB0(),
    CorB0(),
    sorters.B1("b1_ax", seriesdescription="ax_b1map", imagetype="b1"),
    sorters.B1("b1_cor", seriesdescription="cor_b1map", imagetype="b1"),
]

if __name__ == "__main__":
    run(__file__)
