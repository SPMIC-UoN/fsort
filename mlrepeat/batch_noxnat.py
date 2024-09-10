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
#SBATCH --array=28-150
#SBATCH --output mlrepeat/logs/%A_%a.out
#SBATCH --error mlrepeat/logs/%A_%a.err

module load dcm2niix-img
module load renal-preproc-img
module load nnunetv2-img
module load conda-img
module load dcm2niix-img/20190411

source activate renal_preproc

PROCDIR=/spmstore/project/RenalMRI/mlrepeat/proc_20240903
#SUBJIDX=$SLURM_ARRAY_TASK_ID

set -e
for SUBJIDX in {0..50}; do

echo "Processing subject ${SUBJIDX}"
python pipelines/mlrepeat.py --input ${PROCDIR} --dicom dicom \
          --subject-idx=${SUBJIDX} \
          --output ${PROCDIR} --output-subfolder fsort --overwrite  
done

