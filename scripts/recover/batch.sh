#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=recover_fsort
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

module load renal-preproc-img
module load conda-img
module load dcm2niix-img/20211006
source activate renal_preproc

OUTDIR=/spmstore/project/RenalMRI/recover/proc
SUBJIDX=$SLURM_ARRAY_TASK_ID
#SUBJIDX=0

set -e
for SUBJIDX in {7..50}; do

echo "Processing subject ${SUBJIDX}"
XNAT_PASS=`cat /home/bbzmsc/.xnat_pwd` \
    python pipelines/recover.py --xnat-host=https://xnatpriv.nottingham.ac.uk/ --xnat-user=bbzmsc --xnat-project=recover-aki \
          --xnat-subject-idx=${SUBJIDX} --xnat-skip-downloaded --skip-dcm2niix \
          --output ${OUTDIR} --output-subfolder fsort --overwrite  
done

