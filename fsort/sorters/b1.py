import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class B1(Sorter):
    """
    B1 mapping data

    This is quite vendor-specific hence generic implementation
    """
    def __init__(self, name, **kwargs):
        Sorter.__init__(self, name)
        self._kwargs = kwargs
        
    def run_ge(self):
        # GE can be 1 or 2 volume data
        self.add(nvols=2, **self._kwargs)
        self.remove(imagetype="PHASE")
        if self.have_files():
            LOG.info("  - Found 2-volume GE data")
        else:
            self.add(seriesdescription="B1", nvols=1)
            self.remove(imagetype="PHASE")

        # B1 scaling using flip angle?
        self.scale(factor=10, attribute="FlipAngle", inverse=True)
        self.select_latest()
        self.save("b1", vol=0)

    def run_siemens(self):
        self.add(nvols=1, **self._kwargs)
        self.remove(imagetype="PHASE")
        self.scale(factor=0.1) # Siemens data is scaled by x10
        if self.count(imagetype="B1") > 0:
            self.filter(imagetype="B1")
        self.select_latest()
        self.save("b1")

    def run_philips(self):
        self.add(nvols=1, **self._kwargs)
        self.remove(imagetype="PHASE")
        if self.count(imagetype="B1") > 0:
            self.filter(imagetype="B1")

        philips_enhanced = self.count(echonumber=3) > 0
        if philips_enhanced and self.count(echonumber=2) > 0:
            LOG.info(" - Found Philips enhanced protocol - taking echo 2")
            self.filter(echonumber=2)
        else:
            # Philips classic protocol
            self.scale(attribute="PhilipsRescaleSlope", inverse=True)

        self.select_latest()
        self.save("b1")
