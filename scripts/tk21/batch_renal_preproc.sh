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
#SBATCH --array=0-100
#SBATCH --output tk21/logs_rp/%A_%a.out
#SBATCH --error tk21/logs_rp/%A_%a.err

module load dcm2niix-img/20211006
module load renal-preproc-img
module load nnunetv2-img
module load conda-img

source activate renal_preproc

OUTDIR=/spmstore/project/RenalMRI/tk21/proc

SUBJIDX=$SLURM_ARRAY_TASK_ID

for SUBJIDX in {0..100}; do

echo "Processing subject ${SUBJIDX}"
#XNAT_PASS=`cat /home/bbzmsc/.xnat_pwd` \
#    fsort --config pipelines/afirm --xnat-host=https://test-ukrin.dpuk.org --xnat-user=bbzmsc --xnat-project=travelkidney21 \
#          --xnat-subject-idx=${SUBJIDX} --xnat-skip-downloaded  --skip-dcm2niix \
#          --output ${OUTDIR} --output-subfolder fsort_renal_preproc --overwrite --dcm2niix-args="d 9 -b y -m n -f %n_%d_%q -z y"
    fsort --config pipelines/afirm  \
	  --subjects-dir=${OUTDIR} --subject-idx=${SUBJIDX} \
          --nifti=nifti \
          --output ${OUTDIR} --output-subfolder fsort_renal_preproc --overwrite --dcm2niix-args="d 9 -b y -m n -f %n_%d_%q -z y"

done
