# What an Object Is: the RSNA Knee implementation and its evidence

This is an engineering account of the project’s structural computer-vision design,
not a clinical-validation claim or a proof of superiority over other approaches.
The author’s theory governs the representation and reasoning; the experimental
notebook records what particular implementations actually did. Current execution
state belongs only to FULL_BUILD_PLAN §13’s packet.

## The design being instantiated

A knee scan depicts a bounded physical system. Bone, cartilage, ligaments, muscles
and fluid have characteristic organization and relationships. Those relationships
make useful observations and candidate locations much cheaper to obtain than an
unconstrained search. The system uses that structure explicitly: femur and tibia
may resemble one another as bone, while their current-study anatomical arrangement
distinguishes their roles. Appearance need not be forced to distinguish look-alikes.

The anatomical map supplies expectations and supported relations, not a decree
that abnormal anatomy must be rejected. A coarse window is proposed support, not
a certificate of tissue identity. Missing evidence remains unavailable; an actual
contradiction retains its source and scope. Physical non-interpenetration does not
make overlapping sampling windows mutually exclusive anatomical volumes.

The detailed anatomical tools create teaching examples and remain available for
bounded unresolved questions. Production begins with the cheap view and asks for
more information only where the current question needs it. This is the project’s
efficiency mechanism: reuse established facts, reduce the remaining question and
avoid computing irrelevant proxies. The attainable speedup must still be measured
on the complete operation; it is not established by this description.

## One coherent operation

```text
raw MRI series
  -> shared coarse readings and acquisition geometry
  -> current-study anatomical relations and targeted candidate supports
  -> typed multi-view, directional and scale-specific HDC descriptions
  -> contextual identity and normal/condition/configuration recall
  -> condition contracts and applicable negative expertise
  -> warranted answer, or a named bounded observation for an open question
  -> refreshed dependent findings and the twelve output values
```

This is one society sharing one object account. Anatomical placement, identity,
physiological presentation, diagnosis and observation choice are related agency
responsibilities, not separate independent societies. The real entry point is
`scripts/run_interiors.py`; its squint coordinator consumes the shared state.

An object has one identity across its available views. Selected native key planes
retain their acquisition normals and offsets in physical coordinates. Independent
planes can constrain a point; partial or tied evidence remains partial. Geometric
projection between views supplies an addressed search guide. It does not manufacture
a measured outline, certify an inferred object or require every object to possess
three complete views before useful reasoning can occur.

## Exact representation and its limits

The HDC layer uses a512-row Sylvester-Hadamard carrier and exact count-space
operations. Typed banks distinguish measurement, acquisition view, spatial role,
direction and scale. Compatible exact counts support bundling and comparisons
without materializing a dense hypervector for every pixel. Full and cheap
descriptions coexist within a case; an unwritten bank is not measured neutral.

Exactness concerns the retained encoded measurements. A lossy lens does not become
invertible back to the original image merely because its count carrier can be
encoded and decoded exactly. Likewise, a correct measurement does not guarantee
that an anatomical or clinical interpretation of it is correct.

Balanced-ternary meanings remain typed. A negative identity call, an observed
measurement below its reference, a physiological deficit and a condition absence
are different assertions. Healthy physiological zero is not an absent reading;
availability is retained separately.

## Memory and the expressly authorized learned layer

K-lines retain individual contextual precedents, their measured profiles, sources
and scoped calls. Both signs are available in recall. Ordinary negative examples
are immediately useful; a specialized censor or split requires the thesis’s named
significant difference and its justified applicability. A negative label alone does
not automatically become a universal inhibitory rule. A refusal is not a negative.

Corpus construction and parameter training are different connected operations.
Rohan expressly selected three-stage learned navigation over fixed HDC signals:

1. Train subject-domain specialists on independently scoped known targets.
2. Freeze those specialists and train the orchestrator.
3. Refine the composed system jointly at a lower learning rate.

The implementation therefore does include gradient-based parameter fitting for
this authorized layer. It does not fit a replacement MRI encoder or anatomical
definition. The NumPy runtime consumes the exported weights without importing
PyTorch; training uses PyTorch. Memory remains active rather than being discarded
after preparing training data.

The current gate can order existing observation requests, preserving mandatory
work. Its numerical opinions grade unresolved questions. They do not override
warranted symbolic findings or supply independent clinical teaching.

## Diagnosis and evidence authority

Each condition declares necessary, sufficient, alternative and supporting tissue.
Supporting context alone cannot decide an unread defining-tissue question. A
study-level positive fracture or contusion label does not identify every bone as
injured. Configuration wrapping cannot increase the scope of the observations
actually compared. Warranted whole-normal and joint configurations retain the
author’s specified authority.

Changed object observations, identity context or clinical eligibility refresh
already-computed dependent diagnoses. Unrelated and unchanged work stays cached.
This prevents an earlier conclusion from surviving withdrawal of its premise.
It does not prove the premise or a surviving diagnosis clinically correct.

The final output policy is explicit: warranted assigned→1, warranted defeated→0,
open→graded. Raw numerical opinion, internal ranking and final serialized value
are separately attributed. No fitted numerical cutoff creates categorical warrant.
Several conditions can coexist; twelve outputs are not normalized into one
mutually exclusive probability mass.

## What the experiments establish

[Experiment001](experiments/training/001-first-58-study-readback.md) measured a
58-study teaching readback under a922-case memory. It was **not held out**: the
query study could supply its own teaching. Selected results illustrate why both
decisive coverage and errors must be reported:

| Condition | Positive identified / open / wrong | Negative identified / open / wrong | AUC |
|---|---:|---:|---:|
| Lateral OA |2 /9 /0 |8 /39 /0 |0.777563 |
| Contusion |3 /16 /0 |12 /26 /1 |0.794197 |
| Fracture |3 /14 /1 |13 /26 /1 |0.762500 |
| Medial OA |3 /11 /1 |17 /24 /2 |0.762791 |
| Effusion |10 /16 /9 |5 /8 /10 |0.475776 |
| Synovitis |10 /8 /9 |13 /6 /12 |0.542413 |

The notebook reports all twelve conditions. Selective correct decisive calls do
not imply perfect precision over unobserved cases or broad diagnostic coverage.
That historical run recorded1012.48 seconds with four workers and a named peak
RSS measurement of7,432,372,224 bytes. It is not a current-source, hidden-cohort or
combined-process memory guarantee.

[Experiment004](experiments/training/004-three-stage-navigation-pilot.md) records
the later completed three-stage training. Dataset-r2 has106 training and12
development-validation studies; the training set includes all58 official teaching
studies. The model has10,566,320 parameters. Saved teaching-row raw rankings reach
per-condition AUC0.994–1.000, which is training fit, not independent transfer.
Development validation is mixed, and old categorical errors still impair combined
readouts. Validation participated in epoch retention and is not an untouched test.
The repaired raw58-study run was interrupted after four complete records and has
no completed cohort result. Source-pinned receipts and limitations are linked there.

## Verification and operational boundary

The repository provides intent tests, import contracts, mutation/property tools,
coverage, dependency and workflow checks, Sonar correctness checks, and recorded
kernel benchmarks. These tools constrain software behavior; they are not a formal
proof of anatomy or diagnosis. A green suite alone does not establish that a
clinical claim is warranted or that a learned procedure helps a new study.

Reproducible setup and commands are in
[SOM_NAVIGATION_RUN_GUIDE](SOM_NAVIGATION_RUN_GUIDE.md) and
[SQUINT_RUN_GUIDE](SQUINT_RUN_GUIDE.md). MRI data, private conversation records,
signed memories and learned artifacts are retained locally and excluded from git.
A fresh clone requires those explicitly supplied inputs or their documented
construction process; the repository does not secretly bundle them.

The code implements a structural vision and learning mechanism with auditable
observations and demonstrated partial capability. Complete clinical discrimination,
robust abstention on every abnormal presentation, comparative superiority, no
catastrophic forgetting and a final competition-scale resource envelope are not
established by the present evidence. Those claims must be tested separately. No
formal competition submission is authorized by this document or by a successful gate.
