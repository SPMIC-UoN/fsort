#!/bin/env python
import glob
import os
import shutil

PROCDIR = "/spmstore/project/RenalMRI/mlrepeat/proc_20240903"

for subjid in os.listdir(PROCDIR):
    if subjid.endswith("X2"):
        print(f"Found repeat session: {subjid}")
        subjdir = os.path.join(PROCDIR, subjid)
        scandir = list(glob.glob(os.path.join(subjdir, "dicom", "*", "scans")))[0]
        scans = {}
        for scan in sorted(os.listdir(scandir), key=lambda x: int(x[:x.index("-")])):
            #scan_id = int(scan[:scan.index("-")])
            scan_name = scan[scan.index("-")+1:]
            scan_subdir = os.path.join(scandir, scan)
            if scan_name not in scans:
                scans[scan_name] = [scan_subdir]
            else:
                scans[scan_name].append(scan_subdir)
        #print(f"Found scans:\n{scans}")
        r1_dicomdir = os.path.join(subjdir.replace("X2", "_REPEAT1"), "dicom", "scans")
        r2_dicomdir = os.path.join(subjdir.replace("X2", "_REPEAT2"), "dicom", "scans")
        shutil.rmtree(r1_dicomdir)
        shutil.rmtree(r2_dicomdir)
        os.makedirs(r1_dicomdir)
        os.makedirs(r2_dicomdir)
        for scan, repeats in scans.items():
            repeat_names = [os.path.basename(r) for r in repeats]
            if len(repeats) == 2:
                print(f"cp {repeats[0]} -> {os.path.join(r1_dicomdir, repeat_names[0])}")
                print(f"cp {repeats[1]} -> {os.path.join(r2_dicomdir, repeat_names[1])}")
                shutil.copytree(repeats[0], os.path.join(r1_dicomdir, repeat_names[0]))
                shutil.copytree(repeats[1], os.path.join(r2_dicomdir, repeat_names[1]))
            else:
                for scan_subdir, scan_name in zip(repeats, repeat_names):
                    print(f"cp {scan_subdir} -> {r1_dicomdir}")
                    print(f"cp {scan_subdir} -> {r2_dicomdir}")
                    shutil.copytree(scan_subdir, os.path.join(r1_dicomdir, scan_name))
                    shutil.copytree(scan_subdir, os.path.join(r2_dicomdir, scan_name))
        shutil.rmtree(subjdir)



            
                          


