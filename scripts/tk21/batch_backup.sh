#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=tk21_fsort
#NOTSBATCH --partition=imgcomputeq,imghmemq
#SBATCH --partition=imghmemq,imgcomputeq,imgvoltaq,imgpascalq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16g
#SBATCH --qos=img
#NOTSBATCH --gres=gpu:1
#SBATCH --export=NONE
#SBATCH --array=0-50
#SBATCH --output tk21/logs/%A_%a.out
#SBATCH --error tk21/logs/%A_%a.err

module load dcm2niix-img/20211006
module load renal-preproc-img
module load nnunetv2-img
module load conda-img

source activate renal_preproc

OUTDIR=/spmstore/project/RenalMRI/tk21/proc_20240904
SUBJDIRS=/spmstore/project/RenalMRI/backups/travelkidney21/subjdirs.txt

#SLURM_ARRAY_TASK_ID=40
SUBJIDX=$SLURM_ARRAY_TASK_ID
echo "Processing subject ${SUBJIDX}"

fsort --config pipelines/tk21 \
      --subjects-file=${SUBJDIRS} --subject-idx=${SUBJIDX} --subjects-file-has-dirs \
      --dicom . --skip-dcm2niix \
      --output ${OUTDIR} --output-subfolder fsort \
      --overwrite --dcm2niix-args="d 9 -b y -m n -f %n_%d_%q -z y"

