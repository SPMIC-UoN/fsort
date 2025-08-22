"""
FSORT config for AFIRM study
"""
import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class Molli(Sorter):
    """
    T1 MOLLI mapping data
    
    This is quite vendor specific, plus for GE we may only get
    'raw' data that needs subsequent reconstruction to obtain T1 map
    """
    def __init__(self):
        Sorter.__init__(self, "molli")

    def run(self):
        for organ in ["liver", "kidney", "pancreas"]:
            self.add(seriesdescription="molli", imagetype="M")
            self.filter(seriesdescription=organ)
            if not self.have_files() and organ == "liver":
                LOG.info("No MOLLI data found for liver, checking for 'generic' naming")
                self.add(seriesdescription="molli", imagetype="M")
                self.remove(seriesdescription="kidney")
                self.remove(seriesdescription="pancreas")
            if not self.have_files():
                LOG.warning(f"No MOLLI data found for {organ}, skipping")
                continue
            self.select_latest()
            self.save(f"molli_{organ}")
            self.clear_selection()

SORTERS = [
    Molli(),
]
