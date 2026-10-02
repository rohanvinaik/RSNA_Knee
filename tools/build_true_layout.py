"""Assemble data/registered_true/ for the make-or-break instrument.

reference/ = first 50 true normals (sorted; parser-certified all-negative)
normal/    = remaining 30 true normals (held out)
abnormal/  = the 35 Effusion-positive labeled studies (same template space)

Symlinks — no data copied. Template mask carried over unchanged (the
template study is ladder-invariant).
"""

from __future__ import annotations

import shutil
from pathlib import Path


def main() -> int:
    src_norm = sorted(Path("data/registered_normals").glob("*.npy"))
    src_abn = sorted(Path("data/registered/abnormal").glob("*.npy"))
    out = Path("data/registered_true")
    if out.exists():
        shutil.rmtree(out)
    for sub in ("reference", "normal", "abnormal"):
        (out / sub).mkdir(parents=True)
    for i, f in enumerate(src_norm):
        dest = out / ("reference" if i < 50 else "normal") / f.name
        dest.symlink_to(f.resolve())
    for f in src_abn:
        (out / "abnormal" / f.name).symlink_to(f.resolve())
    (out / "template_mask.npy").symlink_to(
        Path("data/registered/template_mask.npy").resolve()
    )
    print(
        f"layout: {min(50, len(src_norm))} reference, "
        f"{max(0, len(src_norm) - 50)} normal, {len(src_abn)} abnormal"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
