#!/usr/bin/env python3
"""
Generate a CSV report of subfolder NIfTI presence per subject.
"""
import argparse
import csv
from datetime import datetime
import os


NIFTI_EXTENSIONS = (".nii", ".nii.gz")


def is_nifti_file(filename):
	filename_lower = filename.lower()
	return filename_lower.endswith(NIFTI_EXTENSIONS)


def folder_has_nifti(folder_path):
	for root, _, files in os.walk(folder_path):
		for filename in files:
			if is_nifti_file(filename):
				return True
	return False


def get_subject_folders(input_dir):
	subjects = []
	for entry in os.scandir(input_dir):
		if entry.is_dir() and not entry.name.startswith("."):
			subjects.append(entry.path)
	return sorted(subjects)


def get_subfolders(subject_path, root_subfolder=None):
	subfolders = []
	base_path = subject_path
	if root_subfolder:
		base_path = os.path.join(subject_path, root_subfolder)
		if not os.path.isdir(base_path):
			return []
	for entry in os.scandir(base_path):
		if entry.is_dir() and not entry.name.startswith("."):
			subfolders.append(entry.name)
	return sorted(subfolders)


def build_report(input_dir, root_subfolder=None):
	subject_paths = get_subject_folders(input_dir)
	all_subfolders = set()
	subject_records = []

	for subject_path in subject_paths:
		subject_id = os.path.basename(subject_path)
		subfolders = get_subfolders(subject_path, root_subfolder=root_subfolder)
		all_subfolders.update(subfolders)

		record = {"subject": subject_id}
		for subfolder in subfolders:
			if root_subfolder:
				subfolder_path = os.path.join(subject_path, root_subfolder, subfolder)
			else:
				subfolder_path = os.path.join(subject_path, subfolder)
			record[subfolder] = "Y" if folder_has_nifti(subfolder_path) else "N"
		subject_records.append(record)

	header = ["subject"] + sorted(all_subfolders)
	return header, subject_records


def write_csv(output_path, header, records):
	with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=header)
		writer.writeheader()
		for record in records:
			for column in header:
				if column not in record:
					record[column] = "N" if column != "subject" else record.get("subject", "")
			writer.writerow(record)


def parse_args():
	parser = argparse.ArgumentParser(
		description="Generate CSV report of NIfTI presence by subject subfolder"
	)
	parser.add_argument(
		"--studydir",
		required=True,
		help="Study directory containing the subject folder",
	)
	parser.add_argument(
		"--folder",
		required=True,
		help="Folder under studydir that contains subject subfolders",
	)
	parser.add_argument(
		"--subfolder",
		help="Only scan subfolders within this folder under each subject (e.g., fsort)",
	)
	parser.add_argument(
		"-o",
		"--output",
		default=None,
		help="Output CSV filename (default: <studydir>/<folder>_report_YYYYMMDD.csv)",
	)
	return parser.parse_args()


def main():
	args = parse_args()
	studydir = os.path.abspath(args.studydir)
	input_dir = os.path.join(studydir, args.folder)
	if args.output:
		output_path = os.path.abspath(args.output)
	else:
		date_str = datetime.now().strftime("%Y%m%d")
		folder_name = os.path.basename(os.path.normpath(args.folder))
		output_path = os.path.abspath(
			os.path.join(studydir, f"{folder_name}_report_{date_str}.csv")
		)

	if not os.path.isdir(input_dir):
		raise SystemExit(f"Input directory does not exist: {input_dir}")

	header, records = build_report(input_dir, root_subfolder=args.subfolder)
	write_csv(output_path, header, records)


if __name__ == "__main__":
	main()
