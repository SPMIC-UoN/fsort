"""
Sorters for T1 data
"""
import logging

import numpy as np

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class T1SERaw(Sorter):
    """
    T1 SE raw mapping data
    """
    def __init__(self, name="t1_se_raw", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        phase_in_fname = False
        self.add(seriesdescription="t1map")
        self.remove(seriesdescription="flipped")
        self.remove(nvols=1)
        self.filter(imagetype="phase")
        if self.count() > 1:
            if self.count(fname="_ph") > 0:
                LOG.info(" - Multiple phase images, using those with _ph in filename")
                self.filter(fname="_ph")
                phase_in_fname = True
        self.select_latest()
        self.save("t1_se_ph")
 
        self.clear_selection()
        self.add(seriesdescription="t1map")
        self.remove(seriesdescription="flipped")
        self.remove(nvols=1)
        self.remove(imagetype="phase")
        if self.count() > 1:
            self.select_latest()
            self.save("t1_se_mag")
        elif phase_in_fname:
            LOG.info(" - Magnitude image not found, trying any images without _ph in filename")
            self.add(seriesdescription="t1map")
            self.remove(seriesdescription="flipped")
            self.remove(nvols=1)
            self.remove(fname="_ph")
            self.select_latest()
            self.save("t1_se_mag")


class T1MolliRaw(Sorter):
    """
    T1 MOLLI raw mapping data
    """
    def __init__(self, name="t1_molli_raw", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        self.add(seriesdescription="t1_molli", nvols=8)
        self.remove(seriesdescription="flipped")
        self.remove(imagetype="phase")
        self.group("affinedata")
        self.select_latest()
        self.save("t1_molli_raw")


class T11MolliMapOrRaw(Sorter):
    """
    T1 MOLLI mapping data or raw MOLLI images if no map available
    
    This is quite vendor specific, plus for GE we may only get
    'raw' data that needs subsequent reconstruction to obtain T1 map
    """
    def __init__(self, name="t1", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def _add_std(self):
        self.add(seriesdescription="molli", imagetype="T1_MAP")
        self.add(seriesdescription="molli", imagetype="T1 MAP")
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="T1")
            self.filter(imagetype="MAP")
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="MIXED")

    def _filter_std(self):
        self.remove(nslices=3, reason="3-slice heart scan")
        self.remove(seriesdescription="500", reason="TD500 scan addition to TD0 scan")
        self.remove(seriesdescription="DelREc", reason="delayed reconstruction")
        self.remove(seriesdescription="6.5", reason="6.5mm slice")
        if self.count(seriesdescription="highres") > 0:
            self.filter(seriesdescription="highres", reason="Not high-res and we have other data that is")
        if self.count(multislice=True) > 0:
            self.filter(multislice=True, reason="Not multi-slice and we have other data that is")

    def run_philips(self):
        self._add_std()
        self._filter_std()

        if self.count(nvols=10) > 0:
            self.filter(nvols=10)
            nvols, map_vol, conf_vol = 10, 1, 3
        elif self.count(nvols=9) > 0:
            self.filter(nvols=9)
            nvols, map_vol, conf_vol = 9, 0, 2
        elif self.count(nvols=2) > 0:
            self.filter(nvols=2)
            nvols, map_vol, conf_vol = 2, 0, 1
        elif self.count(nvols=1) > 0:
            self.filter(nvols=1)
            nvols, map_vol, conf_vol = 1, 0, 0
        else:
            nvols, map_vol, conf_vol = "UNKNOWN", 0, 0

        self.group("affinedata")
        self.select_latest()
        LOG.info(f" - Found {nvols}-volume data from Philips - taking volume {map_vol} for T1 map, {conf_vol} for confidence")
        self.save("t1_map", vol=map_vol)
        self.save("t1_conf", vol=conf_vol)

    def run_ge(self):
        self.add(seriesdescription="t1map", manufacturersmodelname="orchestra")
        if self.have_files():
            # Offline reconstruction of T1 map
            # Slices are wrongly coded as separate volumes
            self.select_latest()
            img = self.selected[0]
            shape = [img.shape[0], img.shape[1], img.nvols]
            data = np.zeros(shape, dtype=img.data.dtype)
            for vol in range(img.nvols):
                data[..., vol] = np.squeeze(img.data[..., vol])
            img.data = data
            self.save("t1_map")
            self.save("t1_conf")
            return
        self._add_std()
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="MDE")
        self._filter_std()
        self.group("resolution")
        if self.groups:
            largest_number = max([len(g) for g in self.groups.values()])
            selected_res = [g for g in self.groups if len(self.groups[g]) == largest_number]
            if len(selected_res) > 1:
                LOG.warn(f" - Multiple resolutions with {largest_number} slices - selecting first")
            self.filter(resolution=selected_res[0])
        self.group("affinedata")
        self.select_latest()
        if self.count(nvols=1) > 0:
            self.save("t1_map")
            self.save("t1_conf")
        else:
            # GE multi volume is raw MOLLI data and needs reconstruction during processing
            LOG.info(" - No single-volume T1 map - saving raw MOLLI data from GE for subsequent reconstruction")
            self.save("t1_raw_molli")

    def run_siemens(self):
        self._add_std()
        self._filter_std()
        self.group("affinedata")
        self.select_latest()
        self.save("t1_map")
        self.save("t1_conf")