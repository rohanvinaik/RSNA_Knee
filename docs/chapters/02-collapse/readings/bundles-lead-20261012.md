# The lead's reading before §3, and an audit of its own vocabulary

Written 2026-10-12 before opening either second reader. The founder's instruction that produced it:

> "Yes, 'convene the body', but don't start drifting into your own personal vocabulary. That's what
> lets you avoid actually sticking to MY words and plan and build some nonsense that fits your
> priors. Everything should be grounded to my actual, literal prompts, most particularly the ones I
> sent towards the beginning of this process about how the production system is supposed to work."

## Where the lead's words are not his — the audit, done first

| the lead has been saying | his actual word, verbatim | standing |
|---|---|---|
| "convene the body" | *"assemble identity on the superposition of all these analyses at each pipeline run"* | **lead's invention.** Replace. |
| "seated member" | *"one person being absent"*, *"the body being seated has sufficient coverage"* | "seated" and "body" are his; "member" is the lead's shorthand. Defensible, flagged. |
| "the standing" between two readings | *"where things conflict"*, *"the places in which they seem to disagree"* | **lead's invention.** The code is `standing_code`. |
| `concur` / `dissent` | *"disagree"*, *"conflict"*, *"agreement"* | `dissent` is near his "disagree"; `concur` is the lead's. |
| "the conclave" | *"assembling a conclave of lenses"* | **his.** |
| "quorum" | *"quorum is a population-wide state"* | **his.** |
| "superposition", "additive" | *"Truth being resolved through superposition means that information is addative"* | **his.** |

The lead is not proposing to rename anything already committed without his word. It is recording
that three of the names in the shipped unit are the lead's coinages, so he can strike them.

## His literal words on what the production system is, which govern §3

These are the prompts he means by "towards the beginning of this process". Quoted, not summarised.

**2026-10-11, on the failure mode this is built against:**
> "agents like you tend to tunnel-vision when there's a hard problem, and build out a mountain of
> code in one arbitrary spot, one function at a time, and sort of lose the thread of *why* the code
> exists, *where* it sits in a greater project pipeline. That makes it impossible to work, since
> there isn't an actual working pipeline, just functionalities in islands, entire unto themselves.
> And it makes efficiency terrible, since things computed for one step are completely forgotten
> about and re-computed from scratch for an entirely different step."

**2026-10-11, on what the scaffold owes — the longest and most specific statement he has given:**
> "We should build the scaffold of the project once, cleanly, correctly. Everything linked to how
> the full pipeline will consume it, the math/compute being done in each step, how it's meant to be
> fit in with the others, what it does, its output (including compute that can be
> shared/optimized/used to calculate one path efficiently, with the proper efficiencies of
> C++/Rust/JIT/etc, that can produce as many outputs as needed as efficiently as possible), a visual
> output that shows the actual reasoning process on images themselves to demonstrate visual
> reasoning, the orchestration of the thesis stages, how each module is set up to do one thing
> (SICP-style), with what it needs to import and put out, the most atomic functions that would be
> able to perform such an operation, the intent and negative specification contract for its
> behavior, and useful hardware and reasoning that isn't module specific, can serve as whole-project
> global tools that might be useful for other processes, etc."

**2026-10-11:**
> "everything registered and consuming/consumed by the main production pipeline, with photo output at
> every state. The full process, the full workflow of the project, managed diligently."

**2026-10-12, the bar he set for the whole run:**
> "You're telling me, right now, that a single study of images can come into the project in a single
> entrypoint and compute everything we've developed in a single end-to-end production pipeline, with
> full telemetry and visual output and everything, and show the combined sum total of all the
> analyses we have in conversation with one another, able to resolve every significant \<object> in
> the visual field as a single-command pipeline process?"

> "this is a production pipeline. Everything connected properly as a coherent instantiation of the
> thesis, as the thesis itself lays out. That's all I wanted"

> "Not a 'small piece', there is no such thing as a 'small piece' of a single object. All of it."

**2026-10-12, the conclave:**
> "They're ALL talking, and what we're doing is assembling a conclave of lenses for the image series
> in each study and parsing out \<objects>."

> "get all the signals to produce legible output from their path whenever we want the pipeline to
> run, and for us to assemble identity on the superposition of all these analyses at each pipeline
> run. THAT'S what I mean by a 'single, production pipeline'."

**2026-10-11, on what an object's representation IS, which is the thing §3 builds:**
> "the actual representation of the physical objects in visual data is a superposition of a
> high-dimensional representation across various physical traits that are defined to exist in
> specific patterns/combinations. A bone is 'bright' and 'smooth' and 'doesn't absorb radiation, so
> imaging bounces back so it shows up on scans' and 'it's straight-ish' and 'takes up most of the
> image space with a GIANT fucking THING that's the center object in the whole image' and 'there are
> two of them, roughly split in the middle' and 'has a defined border'....etc, etc."

And his own figures, which he attached on 2026-10-11 and said were the design:
> "the 'fingerprint' idea is VERY in-line with the thesis. See the attached figures from the
> \<object> thesis about the cell tracking project — VERY much in-line with the design"

## What the lead reads §3 to be, in his terms

`vectors` is the stage where **identity is assembled on the superposition of all these analyses**.
Per `docs/OBJECT_MODEL.md`, which records his figures H2a2 and H2b: an `<object>`'s profile is the
bundle of its places, as **row counts over named banks**, where the knee's lens axis is the
acquisitions, every row is one balanced-ternary digit, and an unwritable bank is carried as a named
absence rather than as rows of zero.

So a bone being *"bright and smooth and straight-ish and giant and one of two split in the middle
and has a defined border"* is, mechanically, a set of rows — and the object is the conjunction
across them, not any one.

## What the lead is NOT sure of, and will not decide

1. **Which banks this build can honestly fill.** Task 3.2 names two. The lead does not know whether
   that list is his or the lead's.
2. **What the `vectors` stage's picture shows**, in his terms. The route says "the count table per
   `<object>`, with unavailable banks visible as unavailable". That is a table, and he has said the
   point of a picture is *"a visual output that shows the actual reasoning process on images
   themselves"*. A table may not satisfy that.
3. **Whether `vectors` is even the next thing.** The lead proposed it. He has not said so.
4. **The dispatch answer** task 3.1 requires before any code: what resolved fact selects the subject
   kind. The lead's previous answer to the sibling question was deleted as unsupported.

## The questions put to the second readers

1. Where, specifically, has the lead substituted its own vocabulary for his, in the shipped
   `members`/`places` unit and in the §3 plan above?
2. Does the §3 reading follow from his quoted words, or from the lead's priors?
3. Does a count table satisfy his picture requirement, or is that a drift?
4. Is `vectors` the next step under his words, or is the lead choosing it?
