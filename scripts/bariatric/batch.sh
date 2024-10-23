#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=bariatric_fsort
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
#SBATCH --output bariatric/logs/%A_%a.out
#SBATCH --error bariatric/logs/%A_%a.err

module load dcm2niix-img
module load renal-preproc-img
module load nnunetv2-img
module load conda-img
module load dcm2niix-img/20190411

source activate renal_preproc

OUTDIR=/spmstore/project/RenalMRI/bariatric/proc_temp
#SUBJIDX=$SLURM_ARRAY_TASK_ID

set -e
for SUBJIDX in {0..50}; do

echo "Processing subject ${SUBJIDX}"
XNAT_PASS=`cat $HOME/.xnat_pwd` \
    python pipelines/bariatric.py --xnat-host=https://xnatpriv.nottingham.ac.uk/xnat --xnat-user=bbzmsc --xnat-project=bariatric \
          --xnat-subject-idx=${SUBJIDX} --xnat-skip-downloaded \
          --output ${OUTDIR} --output-subfolder fsort --overwrite  
done

