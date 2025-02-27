"""
Sorter for MTR data
"""
import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class MTR(Sorter):
    """
    MTR ON/OFF data
    
    This may be in separate ON/OFF files, or a single 2-volume
    file for Phillips
    """
    def __init__(self, name="mtr", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        self.add(seriesdescription="MT", nvols=1)
        if self.count(seriesdescription="_ND") > 0:
            LOG.info(" - Found distcorr data, will use this in preference")
            self.filter(seriesdescription="_ND")
        self.group("seriesdescription")
        self.select_latest()
        self.save("mtr_on", seriesdescription="on")
        self.save("mtr_off", seriesdescription="off")
 
    def run_philips(self):
        self.add(seriesdescription="MT", nvols=2)
        if self.count(seriesdescription="_ND") > 0:
            LOG.info(" - Found distcorr data, will use this in preference")
            self.filter(seriesdescription="_ND")
        self.select_latest()
        self.save("mtr_on_off")
