#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=afirm_fsort
#NOTSBATCH --partition=imgcomputeq,imghmemq
#SBATCH --partition=imghmemq,imgcomputeq,imgvoltaq,imgpascalq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16g
#SBATCH --qos=img
#NOTSBATCH --gres=gpu:1
#SBATCH --export=NONE
#SBATCH --array=28-550
#SBATCH --output afirm/logs/%A_%a.out
#SBATCH --error afirm/logs/%A_%a.err

module load dcm2niix-img/20211006
module load conda-img

source activate renal_preproc

SUBJDIRS=/spmstore/project/RenalMRI/backups/afirm/afirm_subjdirs.txt
OUTDIR=/spmstore/project/RenalMRI/afirm/proc_20240730
#SLURM_ARRAY_TASK_ID=200

echo "Processing subject ${SLURM_ARRAY_TASK_ID}"

fsort --config pipelines/afirm.py \
      --subjects-file=${SUBJDIRS} --subjects-file-has-dirs \
      --subject-idx=${SLURM_ARRAY_TASK_ID} \
      --dicom . --output ${OUTDIR} --output-subfolder fsort \
      --overwrite --dcm2niix-args="d 9 -b y -m n -f %n_%d_%q -z y" 

