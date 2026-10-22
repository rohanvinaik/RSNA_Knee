# Use the hand-defined teaching references

[The picture atlas](../GROUNDED_TEACHING.md) shows the actual negative/positive pair for each
of the twelve condition questions. [seed_categories.json](seed_categories.json) is the authored
definition: object identity, normal and altered meanings, relevant readings, exact source frames,
rough teaching polygons and the visual review. Polygons annotate these examples; they are not
coordinates or recognition rules to copy to other patients.

Current measured workset: `data/readings/grounded-teaching-20261022/references-r3/`.

- `reference_cases.json`: 24 ordinary case records with measured profiles, native territory
  addresses, scoped identity calls, condition calls and complete independent official source rows.
- Twelve PNG pairs: whole native images and the actual supports sampled.
- Twenty-four NPZ files: exact count rows, Hadamard vectors, bank names and native masks.
- `receipt.json`: all named nonproportional bank differences and actual recall evidence.
- `replay.json`: the saved-case replay through the existing case-recall engine.
- `validation.json`: saved-array roundtrips, source pins and verified parent preservation.
- `identity-reference-index.json`: inherited confirmed identity cases for 32 anatomical objects.
  These inherited calls were not all re-reviewed in this task. Their full signed parent remains
  authoritative, including the negative cases; this index does not replace it.

Reproduce from raw studies, using a **fresh** output directory:

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_teaching.py \
  --output data/readings/grounded-teaching-20261022/references-next
```

Replay saved profiles cheaply without rereading MRI data:

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_teaching.py \
  --replay data/readings/grounded-teaching-20261022/references-r3/reference_cases.json
```

`reference_memory(cases, revision)` uses ordinary `prepare_recall` and `recall_object` consumers.
This supplies explicit teaching inputs for the next classical-learning work. It is a reference
workset, not a published child and not silently installed into the full-study inference path.
Any eventual publication must extend the newest signed parent, retaining all prior evidence.

Each query asks about an addressed object-state presentation. A negative at that site does not
silently certify every possible site of a whole-knee condition. The bone-positive cases retain
independent report localization; a study-level fracture label alone does not localize a lesion.

Labels, interpretations and category names are not injected into image measurement banks. The
scan-local low/middle/high coding is not the clinical healthy zero. The normal clinical meaning
is the authored reference and its independently taught presentation. A named count difference is
a measurement, not automatically the explanation of a lesion. Clinical reference and complete
source reports are retained separately from measured features.

Teaching replay checks the supplied examples and the opposing references; it is not held-out
recognition or proof that every study is diagnosed. Use these definitions to interpret further
examples and construct the designed agency-learning experiences. Do not replace that step with
an AUC sweep, altered readout bands or Kaggle packaging. A failed case calls for looking at the
actual tissue and the missing information against the definition.

R1 was withdrawn after image inspection rejected two supports. R2 corrected the pictures; R3
keeps those same pictures and adds ordinary territory and condition-carry records for reuse.

The reviewed workset has now been extended into an immutable signed child through
`scripts/grounded_recognition.py`. [The recognition workflow](../GROUNDED_RECOGNITION.md)
gives publication, actual raw-image inference, the 58-study ledger and picture review commands.
The current packet names the exact authoritative child and measured run; earlier statements
above describe the standalone R3 workset, not the later publication.
