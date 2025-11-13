#!/bin/env python
"""
Convert CSI DICOM files to NIfTI format

This is designed to pretend to be dcm2niix for compatibility with fsort
"""
import argparse
import json
import os

import nibabel as nib
import numpy as np
import pydicom


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            description="Convert CSI DICOM files to NIfTI format",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        self.add_argument("csi_dir", help="Path to the CSI DICOM directory")
        self.add_argument(
            "-o",
            dest="output",
            default=".",
            help="Directory to save the output NIfTI files",
        )
        self.add_argument("-b", help="Ignored for dcm2niix compatibility")
        self.add_argument("-z", help="Ignored for dcm2niix compatibility")
        self.add_argument("-f", help="Ignored for dcm2niix compatibility")
        self.add_argument("-d", help="Ignored for dcm2niix compatibility")
        self.add_argument("-m", help="Ignored for dcm2niix compatibility")


def _get_csi_voxel_data(dcm):
    rows = dcm.Rows
    cols = dcm.Columns
    slices = dcm.NumberOfFrames if "NumberOfFrames" in dcm else 1
    samples = dcm.DataPointColumns
    voxel_data = np.frombuffer(dcm.SpectroscopyData, dtype=np.complex64).reshape(
        (slices, rows, cols, samples)
    )
    voxel_data = np.transpose(voxel_data, (2, 1, 0, 3))  # Convert to (x, y, z, samples)
    voxel_data = np.flip(voxel_data, axis=1)  # Flip PA to match NIfTI orientation

    first_frame = dcm[(0x2001, 0x105F)].value[0]
    origin = [
        first_frame[(0x2005, 0x107A)].value,
        first_frame[(0x2005, 0x1078)].value,
        first_frame[(0x2005, 0x1079)].value,
    ]
    fov = [
        first_frame[(0x2005, 0x1076)].value,
        first_frame[(0x2005, 0x1074)].value,
        first_frame[(0x2005, 0x1075)].value,
    ]
    pixel_spacing = first_frame[(0x2005, 0x107E)].value

    if pixel_spacing == 0:
        return None, None  # No valid pixel spacing, cannot compute affine
    else:
        affine = np.array(
            [
                [pixel_spacing, 0, 0, -origin[0] - fov[0] / 2 + 0.5 * pixel_spacing],
                [0, pixel_spacing, 0, -origin[1] - fov[1] / 2 + 0.5 * pixel_spacing],
                [0, 0, pixel_spacing, origin[2] - fov[2] / 2 + 0.5 * pixel_spacing],
                [0, 0, 0, 1],
            ]
        )

    return voxel_data, affine


def main():
    parser = ArgumentParser()
    args = parser.parse_args()

    for base, folders, files in os.walk(args.csi_dir):
        for csi_file in files:
            csi_file = os.path.join(base, csi_file)
            print(f"   - CSI data file: {csi_file}")
            try:
                dcm = pydicom.dcmread(csi_file)
            except Exception:
                print(f"WARNING: Skipping {csi_file} - not a DICOM file")
                continue

            if "SpectroscopyData" not in dcm:
                print(f"WARNING: Skipping {csi_file} - no spectroscopy data")
                continue

            voxel_data, affine = _get_csi_voxel_data(dcm)
            if voxel_data is None or affine is None:
                print(f"WARNING: Skipping {csi_file} - could not extract affine")
                continue
            if voxel_data.shape[3] == 1:
                print(f"WARNING: Skipping {csi_file} - single volume")
                continue
            if voxel_data.shape[3] >= 300:
                print(
                    f"WARNING: Skipping {csi_file} - too many samples ({voxel_data.shape[3]})"
                )
                continue

            print("   - Saving spectroscopy data")
            series_num = dcm.SeriesNumber if "SeriesNumber" in dcm else 0
            output_filename = f"{series_num}_csi"
            voxel_data_abs = np.abs(voxel_data)
            json_data = {
                "SeriesNumber": series_num,
                "SeriesDescription": dcm.SeriesDescription,
                "ImageType": list(dcm.ImageType),
                "Manufacturer": dcm.Manufacturer.split()[
                    0
                ],  # Bizarrely different in CSI dcms vs MPRAG
                "ManufacturersModelName": dcm.ManufacturerModelName,
            }
            print(json_data)

            nii = nib.Nifti1Image(voxel_data, affine)
            nii.header.set_data_dtype(np.complex64)
            nii.to_filename(
                os.path.join(args.output, output_filename + "_complex.nii.gz")
            )
            with open(
                os.path.join(args.output, output_filename + "_complex.json"), "w"
            ) as f:
                json.dump(json_data, f)

            nii = nib.Nifti1Image(voxel_data_abs, affine)
            nii.to_filename(os.path.join(args.output, output_filename + "_abs.nii.gz"))

            with open(
                os.path.join(args.output, output_filename + "_abs.json"), "w"
            ) as f:
                json.dump(json_data, f)


if __name__ == "__main__":
    main()
