"""Where the workbench's pictures go.

A rendered knee is PIXELS -- derived competition data under the RSNA MIRA licence -- so it goes
under `data/`, which `.gitignore` excludes whole, and never into git (`AGENTS.md`, override 7:
"The data itself (pixels, report text) and bulk derived artifacts ... live in `data/`").

Project-relative, resolved from this file, so a script runs from any working directory and the
picture lands in the same place every time. The earlier scripts wrote into the session scratchpad
by its UUID, which made every recorded picture unreproducible the moment the session ended.
"""

from pathlib import Path

# workbench/render/_out.py -> workbench/render -> workbench -> the project root
PROJECT = Path(__file__).resolve().parents[2]


def pictures_dir() -> Path:
    """The directory this run's pictures go in, created if absent."""
    directory = PROJECT / "data" / "pictures"
    directory.mkdir(parents=True, exist_ok=True)
    return directory
