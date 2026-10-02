"""Validate the II.7 report parser against the 58 explicitly-labeled studies.

The 58 are stratified across all report languages (organizer design) —
they are THE gold gate for the parser. Reports per-finding accuracy,
sensitivity, specificity, and every disagreement with language + evidence
snippet so lexicon growth is error-driven, never speculative.

Usage: python tools/parser_validate.py [--show-errors]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from RSNA_Knee.report_parser import FINDINGS, parse_report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--show-errors", action="store_true")
    args = p.parse_args()

    train = pd.read_csv("data/train.csv")
    manifest = json.loads(Path("data/dicom/manifest.json").read_text())
    labeled = train[train.StudyInstanceUID.isin(manifest.keys())]

    per_finding = {f: {"tp": 0, "tn": 0, "fp": 0, "fn": 0} for f in FINDINGS}
    errors = []
    for _, row in labeled.iterrows():
        parsed = parse_report(str(row.Report))
        for f in FINDINGS:
            gold = int(row[f])
            pred = parsed["labels"][f]
            key = ("t" if pred == gold else "f") + ("p" if pred == 1 else "n")
            per_finding[f][key] += 1
            if pred != gold:
                errors.append(
                    {
                        "finding": f,
                        "gold": gold,
                        "pred": pred,
                        "lang": parsed["language"],
                        "evidence": parsed["hits"].get(f, ["<no hit>"])[0][:100],
                        "report_head": str(row.Report)[:160],
                    }
                )

    total_correct = total = 0
    print(f"{'finding':18s} {'acc':>5s} {'sens':>5s} {'spec':>5s}   tp/fn fp/tn")
    for f in FINDINGS:
        c = per_finding[f]
        n = sum(c.values())
        acc = (c["tp"] + c["tn"]) / n
        sens = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else float("nan")
        spec = c["tn"] / (c["tn"] + c["fp"]) if c["tn"] + c["fp"] else float("nan")
        total_correct += c["tp"] + c["tn"]
        total += n
        print(
            f"{f:18s} {acc:5.2f} {sens:5.2f} {spec:5.2f}   "
            f"{c['tp']:2d}/{c['fn']:<2d} {c['fp']:2d}/{c['tn']:<2d}"
        )
    print(
        f"\nOVERALL cell accuracy: {total_correct}/{total} = {total_correct / total:.3f}"
    )
    print(f"disagreements: {len(errors)}")

    if args.show_errors:
        by_lang: dict = {}
        for e in errors:
            by_lang.setdefault(e["lang"], []).append(e)
        for lang in sorted(by_lang, key=lambda k: -len(by_lang[k])):
            print(f"\n--- {lang}: {len(by_lang[lang])} errors")
            for e in by_lang[lang][:6]:
                kind = "FP" if e["pred"] == 1 else "FN"
                print(f"  {kind} {e['finding']:16s} | {e['evidence'][:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
