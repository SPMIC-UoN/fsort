import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class SeriesDesc(Sorter):
    """
    Sorter matching a series description
    """
    def __init__(self, name, **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        seriesdesc = self.kwargs.get("seriesdesc", self.name)
        fname = self.kwargs.get("fname", self.name)
        self.add(seriesdescription=seriesdesc)
        self.select_latest()
        self.save(fname)
