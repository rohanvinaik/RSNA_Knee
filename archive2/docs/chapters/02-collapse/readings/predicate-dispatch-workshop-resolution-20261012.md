# Task 4.1's dispatch answer: the workshop resolution — 2026-10-12

Three readings, in the order written: the lead's
(`workbench/consults/predicate-dispatch-lead-20261012.md`), then Fable's over the Anthropic API
(`predicate-dispatch-fable-20261012.md`, `claude-fable-5-1`, 2557 in / 5157 out, `end_turn`), then
Codex's (`predicate-dispatch-codex-20261012.md`, GPT-6.1 Sol at high effort). Neither reader saw the
other. Both were given only the lead's question, the lead's understanding and the founder's literal
words.

## Both readers independently found the SAME provable error, so it is evidence

The lead wrote that the fact which would select a predicate's subject **is femur/tibia identity plus
the lateral sign**, and that identity is the founder's to teach.

Fable: *"The first half contradicts the founder verbatim: 'we don't need to be able to link numbered
objects to anatomical roles to do this.' Asserting identity as the required selector reframes the
thesis in the ground of your abstention even though the abstention itself stands."*

Codex: *"The provable error is textual... Your claim that selection requires femur/tibia identity
therefore cannot serve as an established premise here. Missing a described structural selector does
not establish that anatomical identification is necessary."*

**Accepted.** The conclusion (twelve abstentions in this build) survives; its *ground* was wrong, and
wrong in a way that matters — it reintroduced the kind-label framing as the *reason* for the refusal,
which is the dispatch failure wearing the costume of an answer to it. The lead's error, not either
reader's.

**The corrected ground.** The missing facts on the record are structural, and neither is a
kind-label:
- `relations` returns `construction_absent`. No interstice, span or envelope has been constructed, so
  findings 2–11 have no subject of any kind to receive. This is a fact an earlier stage computed and
  reported in the shared absence vocabulary.
- Among several constructed interstices a side sign would be needed to tell them apart. That is a
  *future* selector, not a present blocker, because there are no constructed interstices to tell
  apart.

## A second correction, from Fable alone, which narrows the claim

*"Fracture and Contusion are specified on* a *bone, indefinite. Ownership already yields
integer-indexed T1 extents... Your claim 'no resolved fact selects any subject' is therefore stronger
than the facts support for findings 0–1."*

**Accepted as a narrowing.** `read_ownership` does resolve and index T1 extents. So for findings 0–1
a *candidate* subject population exists. Whether an indefinite subject is satisfied by ranging over
every T1 extent is the founder's ruling, not the lead's — and separately, the predicate's *form*
(what "a break in structural coherence" measures) is recorded in `predicates/__init__.py` as his to
teach. So findings 0–1 abstain too, but for a **different and honest reason**: a subject population
exists and the predicate's form has not been given.

That difference is worth having, because it is the first place where the stage's own record will show
the parse getting ahead of the predicate rather than behind it.

## A third point both readers reached independently: a tier names a category, not a subject

Fable: *"three findings (2, 3, 4) would each abstain with the identical phrase 'a T2 interstice'...
whether a tier that three subjects share counts as naming* the *subject is the founder's to rule."*
Codex: *"A tier names a category, not necessarily the required subject."*

**Accepted as an open ruling, not resolved here.** The stage will name the unmet **structural
requirement**, which is finer than the tier and still carries no anatomy — "an interstice of a facing
pair", "the content of an interstice", "a span attached to two objects", "an envelope", "an
envelope's lining". Findings that genuinely share a requirement will share a reason, and the record
will show that plainly rather than manufacturing a distinction. Whether that satisfies
`abstaining-findings`' *"the reason is not the same for every finding unless the same thing was
missing"* is his to read off the rendered table.

Deliberately NOT done: inventing a non-anatomical discriminator among the three interstitial
findings. That would be meaning supplied by formula where his ruling belongs.

## One correction the lead does not accept, and says why

Codex: *"the record does not establish that the two collapsed outcomes have different remedies. It
establishes three readings."*

This refers to the lead's refusal to write a decided violated/within branch. The lead's ground was
his words *"mostly as a ternary operation (sub-normal/normal/super-normal)"*. Codex is right that
three readings is what that establishes, and the lead's phrasing ("two outcomes whose remedies
differ") was loose. But the conclusion stands on an independent and stronger ground that neither
reader disputed: the expected correspondence `e` has not been supplied, and
`predicates/__init__.py` records each predicate's finer form as the founder's to teach. So no decided
branch is written — not because binary-versus-ternary was settled, but because the comparison has no
declared correspondence to make.

Codex's own closing line supports this: *"Author/date metadata establishes that a declaration exists;
it does not supply the correspondence itself."* Noted as a real limit on what the `e`-declaration
argument buys.

## The dispatch answer, as recorded in `tasks.md`

**No kind-label selects any predicate's subject, so task 4.1 does not stop.** Findings 2–11 receive
no subject because none is constructed (`construction_absent`, computed by `relations`). Findings 0–1
have a candidate subject population — the integer-indexed T1 extents `ownership` resolved — and
abstain because the predicate's form is not given. All twelve therefore abstain, each naming the
structural requirement it did not receive.

## Open, and the founder's to rule

1. May an indefinite subject ("a bone") be satisfied by ranging over every resolved T1 extent?
2. Does naming the unmet structural requirement adequately *name the missing subject* when three
   findings share one requirement?
3. May a predicate record carry the competition's column names, or do those live only in the
   serialiser? (The lead has assumed the latter on `stage-totality`'s literal text.)
4. The form of each predicate, and the form and gating of `e`.
5. **A lead for `knee-object-model` 2.2, not for this task:** Fable asks whether the DICOM header's
   Laterality attribute already supplies the side sign — *"'not computed anywhere' does not mean 'not
   available'."* The project's own measured record says the tag is **absent from 181 of 336 series**,
   so it is present in 155. Whether the study stage reads it was not established this session.
