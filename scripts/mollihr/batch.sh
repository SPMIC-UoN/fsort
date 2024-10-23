#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=mlrepeat_fsort
#NOTSBATCH --partition=imgcomputeq,imghmemq
#SBATCH --partition=imghmemq,imgcomputeq,imgvoltaq,imgpascalq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16g
#SBATCH --qos=img
#NOTSBATCH --gres=gpu:1
#SBATCH --export=NONE
#SBATCH --array=0-5
#SBATCH --output scripts/mollihr/logs/%A_%a.out
#SBATCH --error scripts/mollihr/logs/%A_%a.err

module load dcm2niix-img
module load renal-preproc-img
module load nnunetv2-img
module load conda-img
module load dcm2niix-img/20190411

source activate renal_preproc

DATESTAMP=20241011
DATADIR=/spmstore/project/RenalMRI/mollihr/data
PROCDIR=/spmstore/project/RenalMRI/mollihr/output_${DATESTAMP}

set -e
for SUBJIDX in {0..5}; do

echo "Processing subject ${SUBJIDX}"
python pipelines/mollihr.py --input ${DATADIR} \
          --subject-idx=${SUBJIDX} \
          --output ${PROCDIR} --output-subfolder fsort --overwrite  
done

