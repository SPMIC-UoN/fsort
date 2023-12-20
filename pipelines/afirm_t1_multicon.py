import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class T1multicon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t1multicon")

    def run_ge(self):
        LOG.warn("Ignoring GE data for now")

    def run_philips(self):
        self.add(seriesdescription="MOLLI", nvols=8)
        self.remove(seriesdescription="6.5")
        self.remove(seriesdescription="rptH")
        if self.count(seriesdescription="highres") > 0:
            self.filter(seriesdescription="highres")
        if self.count(seriesdescription="high res") > 0:
            self.filter(seriesdescription="high res")
        if self.count(seriesdescription="high_res") > 0:
            self.filter(seriesdescription="high_res")
        self.select_latest()
        self.save("t1_multicon")
        
    def run_siemens(self):
        self.add(seriesdescription="MOLLI_BH", scanningsequence="GR", nvols=8)
        self.remove(seriesdescription="6.5")
        if self.count(seriesdescription="highres") > 0:
            self.filter(seriesdescription="highres")
        if self.count(seriesdescription="high res") > 0:
            self.filter(seriesdescription="high res")
        if self.count(seriesdescription="high_res") > 0:
            self.filter(seriesdescription="high_res")
        self.select_latest()
        self.save("t1_multicon")
        
SORTERS = [
    T1multicon(),
]
