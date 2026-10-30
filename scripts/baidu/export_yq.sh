#!/bin/bash
# CPU job (Beijing): stage the PFS venv and checkpoints on BOS for the Yangquan A800 pool, which has neither PFS nor
# internet (PyPI, hf-mirror, huggingface and github all time out there; BOS mounts). Yangquan jobs unpack the venv
# at the same absolute path, so the software stack is byte-identical to the Beijing jobs'.
# env: MODELS (default Openvla-oft-SFT-libero10-traj1), dirs under $PFS/models
set -u
PFS=/mnt/pfs/shitianyu-rsi
OUT=/mnt/bos/shitianyu-rsi/yq
mkdir -p "$OUT/models"
ls "$PFS"/envs/vla312-r3/.done-* || { echo "EXPORT_FAILED no finished venv"; exit 1; }
t=$(date +%s)
if tar -C / -czf /tmp/vla312-r3.tgz mnt/pfs/shitianyu-rsi/envs/vla312-r3 && cp -f /tmp/vla312-r3.tgz "$OUT/vla312-r3.tgz"; then
  # the .sha256 marker is written last: Yangquan jobs only trust a tarball that has one
  sha256sum /tmp/vla312-r3.tgz | cut -d' ' -f1 > "$OUT/vla312-r3.tgz.sha256"
  echo "VENV_EXPORTED $(du -h "$OUT/vla312-r3.tgz" | cut -f1) $(cut -c1-16 "$OUT/vla312-r3.tgz.sha256") $(( $(date +%s) - t ))s"
else
  echo "EXPORT_FAILED venv"
fi
for m in ${MODELS:-Openvla-oft-SFT-libero10-traj1}; do
  S=$PFS/models/$m; D=$OUT/models/$m
  [ -f "$S/.download_done" ] || { echo "EXPORT_FAILED model $m incomplete on PFS"; continue; }
  t=$(date +%s); rm -f "$D/.download_done"; mkdir -p "$D"
  ok=yes
  for f in $(cd "$S" && find . -type f ! -name .download_done); do
    mkdir -p "$D/$(dirname "$f")" && cp -f "$S/$f" "$D/$f" || ok=no
  done
  [ $ok = yes ] && cp -f "$S/.download_done" "$D/.download_done" \
    && echo "MODEL_EXPORTED $m $(du -sh "$D" | cut -f1) $(cat "$D/.sha256") $(( $(date +%s) - t ))s" \
    || echo "EXPORT_FAILED model $m copy"
done
echo EXPORT_DONE
