import logging

from fsort import Sorter, run

LOG = logging.getLogger(__name__)


class Mprage(Sorter):
    """ """

    def __init__(self, **kwargs):
        Sorter.__init__(self, "mprage", **kwargs)

    def run(self):
        self.add(seriesdescription="MPRAGE")
        self.remove(imagetype="PHASE")
        self.save("mprage", sort="seriesnumber", embed_sort_attr=True)


class Csi(Sorter):
    """ """

    def __init__(self, **kwargs):
        Sorter.__init__(self, "csi", **kwargs)

    def run(self):
        self.candidate_set = 1  # csi2niix output
        self.add(fname="csi")
        self.save("csi", sort="seriesnumber", embed_sort_attr=True)


SORTERS = [Mprage(), Csi()]

if __name__ == "__main__":
    run(__file__)
