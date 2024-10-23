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

OUTDIR=/spmstore/project/RenalMRI/recover/afirmsubj

#set -e
SUBJID=RECOVER_AKI_72_V3
echo "Processing subject ${SUBJID}"

fsort --config pipelines/recover_t2 \
      --dicom=${OUTDIR}/${SUBJID}/dicom --output ${OUTDIR}/$SUBJID --output-subfolder fsort --overwrite --dcm2niix-args="d 9 -b y -m n -f %n_%d_%q -z y"

