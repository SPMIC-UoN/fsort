#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=demistifi_fsort
#NOTSBATCH --partition=imgcomputeq,imghmemq
#SBATCH --partition=imghmemq,imgcomputeq,imgvoltaq,imgpascalq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16g
#SBATCH --qos=img
#NOTSBATCH --gres=gpu:1
#SBATCH --export=NONE
#SBATCH --array=0-6500
#SBATCH --output demistifi_fsort_log/%A_%a.out
#SBATCH --error demistifi_fsort_log/%A_%a.err

module load dcm2niix-img/20211006
module load conda-img

source activate renal_preproc

DATA_DIR=/share/ukbiobank/Release_1_body/
OUTDIR=/imgshare/ukbiobank/demisitfi_output_fullsets
GROUPSDIR=/spmstore/project/RenalMRI/demistifi/subgroups_new_20240722
#SUBJGROUP=NO_KIDNEY_DISEASE
SUBJGROUP=KIDNEY_DISEASE
GROUPLIST=${GROUPSDIR}/${SUBJGROUP}
OUTDIR="${OUTDIR}/${SUBJGROUP}"
SLURM_ARRAY_TASK_ID=3

SUBJIDX=$((SLURM_ARRAY_TASK_ID + 1))
SUBJID=`sed "${SUBJIDX}q;d" ${GROUPLIST}`
#SUBJID=`head -${SUBJIDX} ${GROUPLIST} |tail -1`

echo "Processing subject ${SUBJID} from group $SUBJGROUP"
sleep 10

fsort --config pipelines/demistifi.py \
      --dicom=${DATA_DIR}/${SUBJID}/Abdominal_MRI \
      --output ${OUTDIR}/${SUBJID} --output-subfolder fsort \
      --overwrite --dcm2niix-args="d 9 -b y -m n -f %n_%d_%q -z y"

