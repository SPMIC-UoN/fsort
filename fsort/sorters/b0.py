import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class B0TwoEchos(Sorter):
    """
    B0 mapping data
    
    We need the phase at two echos. Sometimes we may not have phase data
    so save real/imaginary part if not as this can be reconstructed to phase
    """
    def __init__(self, name="b0", add_removes=[], **kwargs):
        Sorter.__init__(self, name, **kwargs)
        self._add_removes = add_removes

    def _add_std(self, imagetype=None, fname=None):
        if imagetype is not None:
            self.add(seriesdescription="B0", imagetype=imagetype, nvols=1)
        elif fname is not None:
            self.add(seriesdescription="B0", fname=fname, nvols=1)
        removes = ["pcasl", "off-resonance"]
        removes += list(self._add_removes)
        for remove in removes:
            self.remove(seriesdescription=remove)

    def run(self):
        self._add_std(imagetype="PHASE")
        if not self.have_files():
            LOG.info(" - No B0 maps found with phase type, trying filename match")
            self._add_std(fname="_ph")
        select_earliest = self.kwargs.get("select_earliest", False)
        select_one = self.select_earliest if select_earliest else self.select_latest
        if self.have_files():
            self.group("echotime", allow_none=False)
            if any([len(g) > 1 for g in self.groups.values()]):
                LOG.warn("Could not separate B0 phase/mag data - using filename filtering")
                self.filter(fname="_ph")
                self.group("echotime", allow_none=False)
            select_one()
            self.save("b0_phase_echo", sort="echotime")
        else:
            # No phase? Look for real/imag as we can use them to reconstruct phase
            LOG.info(" - No phase maps found - will look for real/imaginary parts")
            have_real, have_imag = False, False
            self._add_std(imagetype="REAL")
            if not self.have_files():
                LOG.warn(" - No real part found")
            else:
                have_real = True
                self.group("echotime", allow_none=False)
                select_one()
                self.save("b0_real_echo", sort="echotime")
                self.clear_selection()
            self._add_std(imagetype="IMAGINARY")
            if not self.have_files():
                LOG.warn(" - No imaginary part found")
            else:
                have_imag = True
                self.group("echotime", allow_none=False)
                select_one()
                self.save("b0_imag_echo", sort="echotime")
                self.clear_selection()

            if not have_real and not have_imag:
                LOG.info(" - No real/imaginary parts found, looking for 3-volume")
                self.add(seriesdescription="B0", nvols=3)
                if self.have_files():
                    LOG.info(" - Found 3-volume files")
                    self.group("echotime", allow_none=False)
                    select_one()
                    self.save("b0_real_echo", sort="echotime", vol=1)
                    self.save("b0_imag_echo", sort="echotime", vol=2)
            elif not have_real or not have_imag:
                LOG.warn("Could not find both real and imaginary parts - data incomplete")

