#!/bin/bash
# Watchdog for auto_resume_fetch.py: relaunch on process death, exit on
# completion. The only stop it can't survive is the machine going down.
# Usage: bash tools/fetch_watchdog.sh   (from the competition root)

cd "$(dirname "$0")/.." || exit 1
source ../../kaggle_env.sh

PY=/Users/rohanvinaik/miniconda3/bin/python3.14
LOG=data/dicom/auto_resume.log

check_complete() {
    "$PY" - <<'EOF'
import json, sys
from pathlib import Path
m = json.loads(Path("data/dicom/manifest.json").read_text())
done = sum(1 for s, meta in m.items()
           if len(list((Path("data/dicom")/s/meta["series"]).glob("*.dcm"))) == meta["n_slices"])
sys.exit(0 if done == len(m) else 1)
EOF
}

for relaunch in $(seq 1 20); do
    if check_complete; then
        echo "WATCHDOG: all studies complete"
        exit 0
    fi
    echo "WATCHDOG: launch #$relaunch of auto_resume_fetch.py"
    "$PY" -u tools/auto_resume_fetch.py >> "$LOG" 2>&1
    rc=$?
    echo "WATCHDOG: runner exited rc=$rc"
    if [ "$rc" -eq 0 ]; then
        echo "WATCHDOG: complete"
        exit 0
    fi
    sleep 60
done
echo "WATCHDOG: gave up after 20 relaunches"
exit 1
