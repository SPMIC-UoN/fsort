#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=recover_t2_fsort
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
#SBATCH --output recover/logs/%A_%a.out
#SBATCH --error recover/logs/%A_%a.err

module load dcm2niix-img/20190411
module load renal-preproc-img
module load nnunetv2-img
module load conda-img

source activate renal_preproc

OUTDIR=/spmstore/project/RenalMRI/recover/output_20240304
SUBJID=RECOVER-AKI_67

#set -e
for SUBJIDX in {0..0}; do
#SUBJIDX=$SLURM_ARRAY_TASK_ID
echo "Processing subject ${SUBJIDX}"

    fsort --config pipelines/recover_t2 --nifti=$OUTDIR/$SUBJID/fsort/nifti \
          --output ${OUTDIR}/$SUBJID/fsort --overwrite 
done

