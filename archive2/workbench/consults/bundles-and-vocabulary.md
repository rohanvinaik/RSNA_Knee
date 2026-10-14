# Consultation: has the lead drifted off the founder's words, and what does §3 actually build?

You are a second reader on a classical-AI computer-vision project. You are **not** being asked to
propose a design. You may report a provable error with its proof, or ask a question. The founder's
words are the oracle of intent and outrank every reading of them, the lead's and yours.

**The founder's instruction that produced this consultation**, verbatim:

> "Yes, 'convene the body', but don't start drifting into your own personal vocabulary. That's what
> lets you avoid actually sticking to MY words and plan and build some nonsense that fits your
> priors. Everything should be grounded to my actual, literal prompts, most particularly the ones I
> sent towards the beginning of this process about how the production system is supposed to work.
> And consult fable/codex before you do anything"

So the primary question is **not** "is this design good". It is: **where has the lead substituted
its own vocabulary and its own priors for what this founder literally said?**

## The thesis, stated so you do not import a different prior

**There is no machine learning in this architecture, and that is load-bearing, not a preference.**
No CNN, no transformer, no fitted weight, no learned embedding, no "small learned component". The
system resolves `<object>`s — *"a resolvable sub-set of the visual field presented to a computer
vision pipeline"* — from the data's own geometry, constructs relations between them, and reads twelve
diagnostic findings as predicates on those objects and relations. Do not propose a model, a
classifier, a learned encoder or a tuned threshold. Anatomy lives in the **design** (it tells the
designer which lens to build) and never in the **record**: no stage writes "femur".

## The founder's literal words on what the production system is

**On the failure mode it is built against (2026-10-11):**
> "agents like you tend to tunnel-vision when there's a hard problem, and build out a mountain of
> code in one arbitrary spot, one function at a time, and sort of lose the thread of *why* the code
> exists, *where* it sits in a greater project pipeline. That makes it impossible to work, since
> there isn't an actual working pipeline, just functionalities in islands, entire unto themselves.
> And it makes efficiency terrible, since things computed for one step are completely forgotten
> about and re-computed from scratch for an entirely different step."

**On what the scaffold owes — his longest and most specific statement (2026-10-11):**
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

**(2026-10-11):**
> "everything registered and consuming/consumed by the main production pipeline, with photo output at
> every state. The full process, the full workflow of the project, managed diligently."

**His bar for the whole run (2026-10-12):**
> "You're telling me, right now, that a single study of images can come into the project in a single
> entrypoint and compute everything we've developed in a single end-to-end production pipeline, with
> full telemetry and visual output and everything, and show the combined sum total of all the
> analyses we have in conversation with one another, able to resolve every significant \<object> in
> the visual field as a single-command pipeline process?"

> "this is a production pipeline. Everything connected properly as a coherent instantiation of the
> thesis, as the thesis itself lays out. That's all I wanted"

> "Not a 'small piece', there is no such thing as a 'small piece' of a single object. All of it."

**The conclave (2026-10-12):**
> "Truth being resolved through superposition means that information is *addative*. Just because one
> lens, one part of the pipeline isn't able to resolve sufficiently, doesn't mean the rest aren't
> able to say anything. They're ALL talking, and what we're doing is assembling a conclave of lenses
> for the image series in each study and parsing out \<objects>."

> "you don't achieve quorum by reading down the attendance list alphabetically and throwing a tantrum
> when 'Abel Ackerman' is out sick again... quorum is a *population*-wide state. It's 'stateless' in
> that at a single instant, you are measuring if the body being seated has sufficient coverage that
> calling the assembly a 'quorum' rather than 'two women who got lost on their way to the bathroom'
> is an accurate description... get all the signals to produce legible output from their path
> whenever we want the pipeline to run, and for us to assemble identity on the superposition of all
> these analyses at each pipeline run. THAT'S what I mean by a 'single, production pipeline'."

**What an object's representation IS (2026-10-12):**
> "the actual representation of the physical objects in visual data is a superposition of a
> high-dimensional representation across various physical traits that are defined to exist in
> specific patterns/combinations. A bone is 'bright' and 'smooth' and 'doesn't absorb radiation, so
> imaging bounces back so it shows up on scans' and 'it's straight-ish' and 'takes up most of the
> image space with a GIANT fucking THING that's the center object in the whole image' and 'there are
> two of them, roughly split in the middle' and 'has a defined border'....etc, etc."

**Keep everything (2026-10-12):**
> "we always keep information we compute. I'll resolve what we report and how we do it, but the
> pipeline should keep everything, including where things conflict"

**On disagreement, the "three-legged stool" (2026-10-10):**
> "when sources of truth are defined as correct but are incomplete but overlapping in their coverage,
> then the places in which they seem to disagree are not noise to wipe away, but are some of the MOST
> informative information we can have"

**On pictures (2026-10-12):**
> "the analysis isn't LITERALLY done off a drawn image... 'Drawing' is just the output of the
> analysis, but since this is visual data, it can most effectively be judged visually, so why not
> print? ... it should be something that can be turned off for an actual competition setting, where
> the output is just the diagnosis ... but it should be absurdly cheap to put out, since it's just a
> printed copy of the analysis that is already required"

## The lead's own vocabulary audit, offered for you to extend or correct

| the lead has been saying | the founder's actual word | the lead's call |
|---|---|---|
| "convene the body" | "assemble identity on the superposition of all these analyses" | lead's invention |
| "seated member" | "one person being absent"; "the body being seated" | "seated"/"body" his; "member" the lead's shorthand |
| "the standing" between two readings | "where things conflict"; "the places in which they seem to disagree" | lead's invention |
| `concur` / `dissent` | "disagree"; "conflict" | `dissent` near his; `concur` the lead's |
| "conclave", "quorum", "superposition", "additive" | all his, verbatim | his |

## What was just built and shipped, so you can judge the drift concretely

The lens stage previously returned ONE reading per acquisition, whose tercile edge pair came from a
population at the end of a chain (quiet population → coil-count identity → dark sigma →
variance-stabilising table → foreground cut → terciles). When the coil identity refused, the lens
wrote silence over the whole acquisition — measured, 3 of 5 acquisitions of one study.

A second structurally warranted population exists (values above the histogram valley that separates
background from tissue), computed before that chain and already consumed by another stage. It
resolves on 5 of 5.

On the founder's ruling ("two members, keep the conflict"), the stage now reads BOTH, retains both
digit maps, and records per place what the two said: `concur`, `dissent`, `first_only`,
`second_only`, `neither_read`, `invalid_measurement`. There is deliberately no code meaning
"resolved". Measured on one real study: coverage 2/5 → 5/5; on one acquisition 3,044,033 concur and
27,967 dissent; on another the edges landed identical and dissent was zero.

## The next step the lead proposes, which may itself be drift

`vectors` (the bundles) — the stage where, per `docs/OBJECT_MODEL.md` recording the founder's own
attached thesis figures H2a2/H2b, an `<object>`'s profile is the **bundle of its places as row counts
over named banks**, the knee's lens axis being the acquisitions, every row one balanced-ternary digit
against a middle, and an unwritable bank carried as a **named absence, never rows of zero**.

The lead reads this as the stage that makes "a bone is bright and smooth and straight-ish and giant
and one of two split in the middle and has a defined border" mechanical: a set of rows, with the
object being the conjunction across them rather than any one.

It is currently unbuilt and not called by the route at all.

## The questions

1. **Where specifically has the lead substituted its own vocabulary or its own priors for the
   founder's words** — in the shipped unit above, and in the §3 reading?
2. Does the §3 reading follow from his quoted words, or from the lead's priors? Quote the words it
   does or does not follow from.
3. His picture requirement is "a visual output that shows the actual reasoning process on images
   themselves to demonstrate visual reasoning". The planned `vectors` picture is a **count table per
   object**. Does a table satisfy that, or is it a drift?
4. Is `vectors` the next step under his words, or is the lead choosing it? He said "there is no such
   thing as a 'small piece' of a single object. All of it." Does that bear on what comes next?
5. What in his quoted words above has the lead dropped, narrowed, or not acted on at all?

Answer from this document alone. Do not run any command or read any file.
