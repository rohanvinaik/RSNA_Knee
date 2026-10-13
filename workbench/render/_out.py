"""Where the workbench's pictures go.

A rendered knee is PIXELS -- derived competition data under the RSNA MIRA licence -- so it goes
under `data/`, which `.gitignore` excludes whole, and never into git (`AGENTS.md`, override 7:
"The data itself (pixels, report text) and bulk derived artifacts ... live in `data/`").

Project-relative, resolved from this file, so a script runs from any working directory and the
picture lands in the same place every time. The earlier scripts wrote into the session scratchpad
by its UUID, which made every recorded picture unreproducible the moment the session ended.

`pictures_dir()`, which resolved and created `data/pictures` for the hand-run probes, went with
them (task 7.1, 2026-10-12): every drawer now takes its output directory from the joined pass and
checks it lies under `data/` against `PROJECT`, so nothing called it and vulture said so.
"""

from pathlib import Path

# workbench/render/_out.py -> workbench/render -> workbench -> the project root
PROJECT = Path(__file__).resolve().parents[2]


class ArgumentRefusal(ValueError):
    """An argument a hand-typed command supplied wrongly — and NOTHING else.

    A renderer's `main()` catches this and turns it into argparse's exit-2 usage error. It must
    never catch plain `ValueError`, because the same renderers raise that for
    `saved_array_digest_mismatch` and for a malformed receipt: a corruption signal dressed as a
    typo is worse than a crash, since the exit status then says the user mistyped something.

    Declared once here rather than per renderer so every drawing module can tell the two apart the
    same way (`every-stage-renders` task 4b.1, the second of its two owed defects).
    """
