#!/bin/sh
module load renal-preproc-img
module load conda-img
source activate renal_preproc

INDIR=/spmstore/project/RenalMRI/mdr/data_20240522/
OUTDIR=/spmstore/project/RenalMRI/mdr/proc_20240522/

for SUBJDIR in ${INDIR}/*; do
    SUBJID=`basename $SUBJDIR`
    echo "Processing ${SUBJID} in ${SUBJDIR}"
    fsort --config pipelines/mdr --nifti ${SUBJDIR}/NIfTI ${SUBJDIR}/MDR --output ${OUTDIR}/${SUBJID}/fsort --overwrite --allow-dupes --allow-no-vendor
done
