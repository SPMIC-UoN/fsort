#!/bin/sh
#SBATCH --time=04:00:00
#SBATCH --job-name=empa_fsort
#NOTSBATCH --partition=imgcomputeq,imghmemq
#SBATCH --partition=imghmemq,imgcomputeq,imgvoltaq,imgpascalq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16g
#SBATCH --qos=img
#NOTSBATCH --gres=gpu:1
#SBATCH --export=NONE
#SBATCH --array=100-200
#SBATCH --output empa/logs/%A_%a.out
#SBATCH --error empa/logs/%A_%a.err

module load conda-img
source activate renal_preproc

#SLURM_ARRAY_TASK_ID=4
OUTDIR=/spmstore/project/RenalMRI/empa/diffusion_overlay
#INDIR=/spmstore/project/RenalMRI/empa/output/xnatpriv/
INDIR=/spmstore/project/RenalMRI/empa/output/xnatpub/

for SUBJDIR in $INDIR/*; do
    SUBJID=`basename $SUBJDIR`
#    echo "Processing $SUBJID"
#    fsort --config pipelines/empa.py --nifti $SUBJDIR/nifti --output ${OUTDIR}/$SUBJID --overwrite
  for SESSDIR in $SUBJDIR/*; do
      SUBJID=`basename $SUBJDIR`_`basename $SESSDIR`
      echo "Processing $SUBJID"
      fsort --config pipelines/empa.py --nifti $SESSDIR/nifti --output ${OUTDIR}/$SUBJID --overwrite
  done
done
