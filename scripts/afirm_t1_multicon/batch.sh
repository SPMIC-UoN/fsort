#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=afirm_t1_multicon_fsort
#NOTSBATCH --partition=imgcomputeq,imghmemq
#SBATCH --partition=imghmemq,imgcomputeq,imgvoltaq,imgpascalq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16g
#SBATCH --qos=img
#NOTSBATCH --gres=gpu:1
#SBATCH --export=NONE
#SBATCH --array=0-600
#SBATCH --output afirm_t1_multicon_logs/%A_%a.out
#SBATCH --error afirm_t1_multicon_logs/%A_%a.err

module load dcm2niix-img
module load renal-preproc-img
module load nnunetv2-img
module load conda-img

source activate renal_preproc

OUTDIR=/spmstore/project/RenalMRI/afirm_t1_multicon/proc
INDIR=/spmstore/project/RenalMRI/fsort_test/afirm/proc
#SUBJIDX=$SLURM_ARRAY_TASK_ID

for SUBJDIR in ${INDIR}/*; do
    SUBJID=`basename $SUBJDIR`
    echo "Processing ${SUBJID} in ${SUBJDIR}"

    fsort --config pipelines/afirm_t1_multicon.py \
          --nifti ${SUBJDIR}/fsort/nifti \
          --output ${OUTDIR}/${SUBJID} --output-subfolder fsort --overwrite  

done
