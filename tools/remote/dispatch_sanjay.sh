#!/bin/bash
# Dispatch a registration batch to the `sanjay` worker (see ~/.ssh/config).
#
# Design contract (screen-close stable):
#   - runs detached under nohup + caffeinate -is on the remote: survives SSH
#     disconnect, this Mac sleeping, and WiFi blips
#   - lid-close survival additionally needs `sudo pmset disablesleep 1` on the
#     remote (NOPASSWD sudoers entry for /usr/bin/pmset; enable_lidclose below)
#   - resumable: register_normals.py skips studies whose output .npy exists,
#     so re-dispatch after any interruption continues where it stopped
#   - pull results with `pull`; worker never pushes
#
# Usage:
#   dispatch_sanjay.sh ship <dicom-pool-dir> <study-id>...   # sync code+studies
#   dispatch_sanjay.sh run <pool-name>                       # start detached batch
#   dispatch_sanjay.sh status <pool-name>                    # log tail + counts
#   dispatch_sanjay.sh pull <pool-name> <local-out-dir>      # rsync results back
#   dispatch_sanjay.sh enable_lidclose | disable_lidclose    # pmset toggle
set -euo pipefail

HOST=sanjay
WORK='~/rsna_worker'
cmd=${1:?usage: ship|run|status|pull|enable_lidclose|disable_lidclose}

case "$cmd" in
ship)
  pool_dir=${2:?pool dir}; shift 2
  pool=$(basename "$pool_dir")
  rsync -a tools/register_and_export.py tools/register_normals.py "$HOST:rsna_worker/tools/"
  rsync -a data/dicom/manifest.json "$HOST:rsna_worker/data/dicom/"
  # template study series (ladder-invariant; register_normals rebuilds it)
  T=$(/Users/rohanvinaik/miniconda3/bin/python3.14 -c "
import json
m = json.loads(open('data/dicom/manifest.json').read())
print(sorted(s for s in m if m[s]['labels']['Effusion'] == 0)[0])")
  rsync -a "data/dicom/$T" "$HOST:rsna_worker/data/dicom/"
  ssh "$HOST" "mkdir -p rsna_worker/data/$pool rsna_worker/out_$pool"
  for s in "$@"; do rsync -a "$pool_dir/$s" "$HOST:rsna_worker/data/$pool/"; done
  # manifest restricted to the shipped slice — remote todo == shipped studies
  /Users/rohanvinaik/miniconda3/bin/python3.14 -c "
import json, sys
m = json.loads(open('$pool_dir/manifest.json').read())
json.dump({s: m[s] for s in sys.argv[1:]}, open('/tmp/slice_manifest.json', 'w'))" "$@"
  rsync -a /tmp/slice_manifest.json "$HOST:rsna_worker/data/$pool/manifest.json"
  ;;
run)
  pool=${2:?pool name}
  ssh "$HOST" "cd rsna_worker && nohup caffeinate -is venv/bin/python -u \
    tools/register_normals.py --dicom-dir data/$pool --out-dir out_$pool \
    --workers 6 > run_$pool.log 2>&1 & echo \"started pid \$!\""
  ;;
status)
  pool=${2:?pool name}
  ssh "$HOST" "tail -3 rsna_worker/run_$pool.log 2>/dev/null; \
    echo -n 'done: '; ls rsna_worker/out_$pool/*.npy 2>/dev/null | wc -l"
  ;;
pull)
  pool=${2:?pool name}; dest=${3:?local out dir}
  mkdir -p "$dest"
  rsync -a "$HOST:rsna_worker/out_$pool/" "$dest/"
  ;;
enable_lidclose)  ssh "$HOST" 'sudo -n pmset disablesleep 1 && pmset -g | grep -i sleepdis' ;;
disable_lidclose) ssh "$HOST" 'sudo -n pmset disablesleep 0 && echo "normal sleep restored"' ;;
esac
