module load dcm2niix

DATADIR=/home/bbzmsc/data/daniel_c/2H_data
OUTDIR=/home/bbzmsc/data/daniel_c/2H_output

set -e

for SUBJIDX in {0..7}; do
echo "Processing subject ${SUBJIDX}"
    python pipelines/csi.py \
      --input ${DATADIR} \
      --subject-idx ${SUBJIDX} \
      --output ${OUTDIR} \
      --dcm2niix dcm2niix /home/bbzmsc/code/fsort/pipelines/csi2niix.py \
      --overwrite
done

