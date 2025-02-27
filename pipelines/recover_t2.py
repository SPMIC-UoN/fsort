"""
FSORT config for recover t2 mapping
"""
import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class T2(Sorter):
    """
    T2 mapping data
    """
    def __init__(self):
        Sorter.__init__(self, "t2")

    def run(self):
        """
        T2 data has 10 echos but may have 11 vols (last is T2 map - ignore)
        """
        for desc in ("t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"):
            self.add(seriesdescription=desc, expected_number=(10, 11))
            self.remove(echotime=None)
            if self.have_files():
                break
        if not self.have_files():
            LOG.warn("No T2 mapping data found")
        if self.count() == 11:
            LOG.info(" - 11 echos found - trying to remove T2 MAP image")
            self.remove(imagetype="T2 MAP")
            if self.count() == 11:
                LOG.warn("Have 11 echos still")

        self.save("t2_e", sort="echotime")

SORTERS = [
    T2(),
]
