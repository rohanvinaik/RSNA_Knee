# The founder's words — verbatim

These are the operator's own messages behind this book, extracted programmatically from the session transcript
(`~/.claude/projects/-Users-rohanvinaik-Projects-Kaggle-Killer-competitions-RSNA-Knee/144c178d-bd07-4bb9-9f58-661af347e125.jsonl`).
They are byte-exact, typos included, and carry their UTC timestamps. They win over everything else in this book
(`AGENTS.md` → *Where truth lives*).

The earlier canon is not repeated here. It is carried by:
- `docs/FOUNDING_RECORD.md` (2026-08-18);
- the 2026-10-02 morning rulings recorded verbatim in `docs/canon/SESSION_BRIEF_2026-10-02.md` §3;
- the founder's SICP statement of 2026-08-31 in `~/tools/Detective/docs/theory/deterministic_sicp/DETERMINISTIC_SICP.md`
  §1.1, quoted in part below.

## 2026-10-02 — the review

> **07:55:03Z** Can you take a look at the big document there? The "KNEE_ARCHITECTURE" document, as a thesis for
> how the project should be built? Work through the idea, see what you think. Check the referenced documentation
> if you need, and consult with Codex, according to the guidance from global CLAUDE.md, with a writeup of your
> understanding and the general epistemology/approach of the project and other context overall, come to an
> agreement on the design, tell me what you think

That review's record is `provenance/review/`. Its outcome is the ten agreed changes carried by `THE_KNEE.md`
§2.

## 2026-10-02 — the build

> **15:24:53Z** There's a kaggle key in the "kaggle_killer" repo level you can use. The questions should be
> resolved by building and observing, but your recommendations are generally in line with the intent. The bad
> stubs should be retired
>
> In global CLAUDE.md, there's a whole list of tools for digging into how a function works, how code is
> written, code quality, and the considerations when using python vs rust vs C/C++ for different operations.
> It's important to think through what the best, most effective compute operation is for a task (e.g. for
> hypervectors, cache/memory operations can really speed stuff up, and JIT is basically a requirment). ACTUALLY
> look into it. Don't read the pointers in global CLAUDE and feel all satisfied--they're POINTERS, you READ what
> they point to. I'd also like to note that detective is a load-bearing tool to use, but use the one that's
> local, not the one that's installed from PyPI. Still follow the same instructions that global CLAUDE.md
> points you to. Lastly, in the "SquishOS" project, a full build plan is persisted past a session by writing it
> out as a "book", with each severable module as a "chapter", with the full intent and context laid out cleanly
> and persistently. I'd like us to use that. Once you read up on and understand what I mean by all the things
> I've said in this paragraph, I'd like you to write the key/useful rules that you can derive from it in a
> robust CLAUDE.md file in this project level, so you keep in mind the key apprach and how we should generally
> operate when working here to build a nice, best-language, interoperable, and clean, SICP-style codebase
> that's well-organized and fully mutant-pinned through Detective.
>
> You should have everything you need for us to do that. Consult with codex on the exact design, then I think
> we can build out the plan, with each module in its best language, everything guided by the right tooling, and
> it all set up to be persistent past this session's context! Come to me if anything is genuinely uncertain, or
> you need me at the keyboard to set something up or whatever, but you shouldn't

(A first send at 15:24:01Z differed only by lacking "ACTUALLY look into it. Don't read the pointers in global
CLAUDE and feel all satisfied--they're POINTERS, you READ what they point to." The 15:24:53Z text above is the
one that stands.)

Four more messages arrived mid-turn, while the work was under way:

> **15:28:18Z** Cell tracking isn't always perfect, but it's a good start

> **15:28:43Z** We should design things fresh, only use older stuff when it's genuinely the best approach

> **15:34:14Z** Also get Codex to read your "chapters" and grounding context. If you've done it right, then
> codex--literally a different agent--should agree with you about how things should be done

> **15:47:57Z** Oh right, aslo, for heavy compute, I have the Mac Pro sitting around. SquishOS has it registered,
> including how to access and use

## 2026-10-02 — after the compaction: the typist, the fresh read, the revision

> **16:08:14Z** (mid-turn) Nuts, hit the compact. Well, hope you did it well, and it's truly persistent past the
> session context, lol
>
> What do you think about starting up a small local model--"Uroboros" project-style--with a contract/intent tests
> and a specific, gated scope of operation and constrained output to do the mechanical work/code for a large chunk
> of the actual codebase? Then you can come in and professionalize it, make the thing actually work and work well.
> But do you think the literal typing can be handed off to Qwen 3.5B? You tell it what it should type, what
> language/design/etc, detective constrains it output to what the CLI mandates, Qwen (with an Uroboros-style
> harness) types only that which is explicitly authorized by you and detective, mandated by contract and
> constrained output?

> **16:18:17Z** (mid-turn) That's a lot of changes for a fresh-context agent to make. Can you go over what codex
> said, so we can think it through properly?

> **16:19:48Z** (mid-turn) Agree with your "uroboros" claims/ideas, worth working them un

> **16:29:22Z** I take it back--Codex really landed a good one here. Agree with your "acceptance bars", though note
> this is a process of discovery and development, so the "bars" might not look so good for a long time, and fixing
> it is a problem to solve, not a design to discard or work around
>
> Make sure that the re-write is formally grounded in some section of the architecture document, and where
> under-specified, from the original thesis document on computer vision ("what_an_object_is"), or the reference
> manifest. I'm fine adding stuff to git, and make sure the new design sent to codex includes the typist additions

> **16:35:20Z** I did NOT tell you to launch sub-agents. I want YOU to do this. This is CRITICAL. Why would you
> think that was okay?? We are lITERALLY establishing the persistent, post-compact stable context grounding. Why
> would you do that WITH agents that have no prior crounding or global context? That's a FUNDAMENTAL violation of
> the entire POINT of this whole task

(A first send at 16:35:05Z was cut off by an interruption; the 16:35:20Z text stands. It answered three grounding
sub-agents launched at 16:33Z. They were stopped before reporting, and nothing of theirs was used.)

## 2026-10-02 — the engineering tools and the language of each module

> **17:14:12Z** (mid-turn) Also, general guidance, anytime you need to use or reference the developer/code
> understanding/SICP tools, global CLAUDE.md has the pointers you should read, and SquishOS is the home of a lot
> of useful references

> **17:22:59Z** Can tou read my prompts again? I feel like, if you didn't have those tools written up fully, we
> didn't properly address the full scope of actual engineering tools we have available, and considerations about
> language-specific modules (e.g. C/C++ for memory management, cache hot vs cold management, Rust for speed,
> etc). Those tools should help us build in those considerations and implementations from the start, and it's
> worth considering properly

> **17:29:45Z** (mid-turn) We don't have to abandon Radon. It's just an independent tool to use

> **17:30:14Z** (mid-turn) LintGate is over-engineered and super bloated--ironically enough--so Randon is probably
> better

> **17:32:09Z** (mid-turn) Good targeting, but don't assume too much what is and isn't a "cheap" operation "not
> worth optimizing". (1) you don't know what the full/final design, since I don't know it myself, things can change
> a lot as we experiment, and (2) I want this to be AS clean and efficient/professional as possible. This is a
> demonstration, a BOLD claim about classical AI, I want it to be clothed as professionally and impressively as
> possible

> **17:32:17Z** (mid-turn) Suit and tie, not just "not naked"

## 2026-10-02 — after the second compaction: when Codex stops, the global changes, K14

> **17:36:57Z** (mid-turn) Damn, hit the compact AGAIN. Before we continue, a pause for re-grounding? Don't do
> anything specific, just tell me what you think we are doing right now, and what's left for us to complete in this
> whole project setup process. I think we're almost done with setup, I'd like to know what you think is left to do

> **22:42:24Z** Good stuff! The Codex should stop when it should stop. That seems circular, but it should be pretty
> obvious. Codex is for stress-testing your ideas/understanding. When it no longer tells you anything substantially
> useful, or when you know how to properly and completely address what it is saying, or the answer is something
> that's best left to operator intent (me), then we stop.
>
> Take a quick look back into the global context files. I've made some changes/additions that are worth looking
> into/seeing how they might impact your process here.
>
> Then it's time to think through the build. First, REALLY think about that change you made to K14. It's VERY likely
> that it wasn't warranted by the actual theory/design and you'll need to revert, but confirm properly. Then we can
> go through and finish codex's revision 2 (make sure you've actually read it, directly, in this post-compact
> session). THEN, we can get to the real project

> **22:52:11Z** (mid-turn) Yes, now that you're reading the full thesis, I think you can see why I find post-compact
> summaries rather insufficient for design work

(Between 17:36Z and 22:42Z the founder changed the global context at its source, SquishOS `ops/agents/`, commits
`0cd3f4c`…`d94d04a`. What they change here is recorded in `provenance/build/revision_2.md` → *The global changes*.)

## 2026-10-02 — the authority over the design

> **23:06:50Z** (mid-turn) Make sure you're not hallucinating "evidence" and warrants for design. Remember--we haven't
> built this. We're designing it. We have no proof of anything

> **23:08:47Z** (mid-turn) We have ZERO evidence of anyhting outside of pure theory. *I* am the authority on what works
> or doesn't. You don't understand the design. Something that LOOKs like it doesn't work well might actually be
> CRITICALLY important. You do not have the authority to change the design *I* built based on a random guess, when
> you don't know the intent

> **23:09:14Z** Make SURE you are not changing anything other than that which is definitevely/provably correct, or
> warranted by my explicit words

> **23:12:14Z** (mid-turn) Not just this session--EVERY change to the original design

> **23:14:44Z** (mid-turn) And make sure you bonk codex, next time you engage with it. It was a key part of why this
> happened, and it's VERY bad. It's a complete artifcact of hallucination. For the most part, the code *doesn't
> exist*. Forget a warrant of intent that I didn't give, there is LITERALLY not an actual functional codebase that
> meets the design intent

> **23:22:50Z** That doesn't deserve/need feedback. You were within tolerable parameters. I gave codex implicit
> authority on design. It was provisional, you should have been conservative about running with it, but it's not an
> overt failure on your part. On your readings, yes, my warrant was general and high-level, not open authority. And
> the competition's literal data and framing is acceptable, not implicit warrants on design or conception.

## 2026-10-02 — the lens principle

> **23:50:20Z** When I say that no single lens is allowed to have a warrant, complete unilateral authority on a
> decision, I am saying something very explicitly grounded in information theory. This is a thesis based on the work
> I did in the "what is an <object>" thesis on computer vision. Specifically, lenses that are intentionally lossy,
> that do not encode a specific 1:1 relationship to a specific element of "truth", do not have authority to warrant
> a decision unilaterally. A lens is an instrument, an artifact of observation. It does not say "this is the purpose
> of <X>". It simply measures, says things like "the intensity is <X>" or "the variance of the signal in this
> location is increasing with a directional vector of <x,y>". The interpretation is a construction on top of them.
> If the *meaning* of what they observe is definable, then it is encoded as such. So, the answer to question 1 is
> dependent on what you define as "direction", "exclusion", and "lenses". A measurement is different from a
> statement of truth. Properly-designed lenses are never wrong, by definition. They only measure something, a
> specific and objective fact of the problem space. The reason why this is described as "computer vision" is because
> we assign an interpretation of what these signals mean. The "<object>" thesis really goes into depth about this
> with the worked example of cell microscopy
>
> On "the halo", again, this is where the information-theoretic concept here is really important to understand. A
> halo can be both. Are you trying to see if there's an active fracture? Well, fractures have concomitant edema when
> they're relatively fresh, no? So in that case, it's actually *part* of what assigns meaning to other lenses that
> see something that looks kind of like a fracture but can't fully warrant. But when it comes to the question of
> "what are the specific <x,y> coordinates of the line-drawing process that traces the exact fracture, then edema is
> noise to remove. The point here isn't to find some clean metric that hands you the perfect and complete answer.
> This is the core part of why and how this is a deterministic and classical AI computer vision approach. Meaning is
> derived from structure, not computed from some magical metric that solves everything.
>
> This should also address "independence classes". The answer to "A ≇ B", "B ≇ C", and "A ≠ C" is "yes". That's not
> a contradiction, it's a finding. The epistemology of deterministic approaches to machine intelligence is
> principled abstention--you know what you know, you know what you don't know, and those are both complete and
> correct assertions of the process of reasoning
>
> I think this is rather enough to get started. Think about it, think through the theory this is based on and how it
> informs your understanding of the whole project, and take it to codex too to work it out. Then, we see what we
> need to change about the project design to properly adhere to this load-bearing principle

## 2026-10-02 — what a Codex consultation is

> **23:56:22Z** No, not the full thesis. Codex is meant to be a minimal common-sense check, not a dump. The whole
> point is that you can drift in understanding by having an overloaded context window, but a fresh look assigns
> significance differently, so can catch you if you're missing something important and/or obvious
>
> You are only supposed to include your question/understanding and my literal words, to maintain maximal semantic
> purity for the reasoning operation

(A first send at 23:55:42Z, the first paragraph alone, was interrupted; the 23:56:22Z text stands. It answered a
plan to send Codex the whole thesis with the lead's reading.)

> **23:59:57Z** (mid-turn) Note this principle will even supercede the atchitecture document as well. The concept is
> the rigid oracle, the design is something we're working on building in session

## 2026-10-03 — the lens principle, defined

> **00:10:18Z** 1. I'm not sure what those three words specifically reference without context
> 2. Yes, "≇" was meant to imply a statement of truth that some lenses seem to *imply*, but cannot formally warrant,
> and so the mutual exclusivity of those categories as assignments to a particular problem/object is not known.
> "Seems like they're different" is not the same as "these are different". Your question was about knowable
> mutual-exclusiveness vs that which is only vibes-y
> 3. Yes. If defined carefully. A single lens can assign a value (or assign that something is *not* <X>--knowing
> that something is "<not> X" is as much a statement of truth as knowing something *is* X), but only if it is
> inherently a measurement of truth. A "lens" can measure that a set contains the integers [3,5,7], and that can be
> the same as the assignment of truth that "this set only contains odd, prime numbers". It CANNOT assert that "this
> set will always contain only odd, prime numbers". But if ANOTHER lens says that the set is complete as is, THEN we
> can. Both are statements of truth, both can be warranted. The first is sufficient with just the one lens. The
> second is warranted as well, but the truth is a CONJUNCTION of both lenses, with an interpretation provided by the
> structure of the problem space (And me, you with my approval).
>
> Sounds good? Makes sense?

> **00:18:12Z** Correct. We can assign +1/0/-1 for both. For a lens that speaks to correctness and a strict warrant,
> that can mean "assignment/abstention/rejection". For one that is directional only, an assignment that is a
> statement of truth/understanding beyond the reach of any objective single lens, it can mean "evidence
> for/abstention/evidence against", and the truth table is an explicitly encoded operation in balanced ternary, a
> strictly defined subset of the truth table, possibly (likely, for complex assignment) more than one single path to
> truth. You see the elegance of the whole design, yes? Hypervectors and HDC seem kind of overwrought, the way we
> use them. But they are *literally* matrix math operations across intentionally-defined banks, which is basically a
> fancy version of a giant truth table. Make sure to take it to codex in that chat you just opened, make sure you
> both understand it fully.
>
> I actually rather like this whole framing, this and the past message. I'd later like to add it in to the
> "<object>" thesis. Mind adding that as a memory or gh issue in the "cell_tracking" project?

> **00:27:25Z** 1. That's what building this project is meant to answer. That's based on biology, on medicine, and
> on physics and math. What the "lenses"/the data we're given *actually* measure, vs what that means and how it
> informs our understanding of "truth
> 2. Yes, that is the mechanism of concurrence. Because, I mean, that *is* what a committe is. Not a democracy. Not
> a dictatorship. A committee is something that makes decisions, period. It can make a positive decision, a negative
> decision, an ambiguous one, or even make a majority decision with a noted dissention that has a different
> conclusion. All are valid and sane outputs of a committee process, which is why it's the framing for how this is
> built.
> 3. Oh no, not at all. In fact, dissention between lenses that are otherwise positively correlated can be some of
> the most *valuable* pieces of data. Again, this project is *deeply* instantiated in information theory. The enemy
> isn't correctness or noise, it's *entropy*. A thing that is wrong or that is noisy with a legible trace of
> reasoning behind it *is* information. The work of this project is not to discard the noisiness of the real world,
> but to incorporate it and learn what it means. Hence why we have classical AI in the loop, and don't just build
> one "God script" in python and call it a day

> **01:33:48Z** 1. No, that's the wrong kind of assignment of meaning. We don't classify "lesion" and "normal". We
> classify according to definable categories of image, the way images are able to be resolved into meaningful
> buckets that are mutually-exclusive. Like the "noise", "cell", "not-noise but not-cell" (note the
> subtlety--"not-noise not cell" was only allowed to reject noise as an option, abstained on the question of cell or
> no. *Strict* boundaries of knowability, always). What those categorizations *mean* is a question for a
> fluid-intelligence oracle to rule on (hi. is me)
> 2. Yes. Most important is to make the code actually work, to be built. I ascribe meaning to it when I literally
> see it in action. So "what we have to establish" is itself...something we have to establish
> 3. On the five:
> 3-1. ARCH 5.3 is not wrong as a principle, it is wrong as a law. Amusingly enough. You have a bad habit of finding
> a set of signals that kinda vibe and jumping to assign a label to it. "Majority vote" isn't the thing that assigns
> correctness, but a majority *can* be a sufficient contract that decides on a ruling, comittee style. Essentially,
> this isn't upwards-looking ("how many singals can come together to get us an answer?"), but downwards-looking
> ("how many violations of which strength signals is enough to cause an assignment to fail?"). Essentually,
> near-miss learning!
> 3-2. We measure indepenedence, and that certainly is essential to how we assign meaning to the combined verdicts
> of these signals, but correlation isn't damning in and of itself. Again, you see the *elegance* of HDC and vector
> math? How delightfully compatible are vector operations, cosine similarity, and correlation between lenses?
> 3-3. Agreed. We need to be THOROUGH about what passes the gate for what can speak to strict exclusion, but when we
> find one, we can use it *confidently*. That's the "black" and "speck" filter from the cell microscopy work in the
> "<object>" thesis--two lenses that are correct negative signals for "Cell" assignment, so we can just wipe out the
> field for most of the heavy compute for about half the problem space!
> 3-4. Same
> 3-5. The word is "near-miss learning" :3. That's not the *whole* thing, of course. There are some elements that
> are deterministic, not pure AI. But it was too cute of a homology to not use
>
> I actually really enjoy talking information theory with you! You're *definitionally*, by the very core of your
> nature as a neural net, opposed to determinism and strict bounds of information theory. You're simultaneously very
> smart and eloquent but also charmingly ignorant/lacking in intuition about knowability and correctness and
> "common-sense" deterministic reasoning. I enjoy explaining and living in this mental space regardless, and always
> enjoyed teaching/explaining things, so it works out very well. Plus, it makes my design MUCH better when I explain
> things to you.
>
> Check in with codex again with this explanation, make sure the epistemology here is *rigorously* clear to all
> three of us

## 2026-10-03 — the oracle front and center; an independent understanding before the architecture

> **01:39:36Z** We should also make sure this is front and center wherever relevant. CLAUDE.md, general
> grounding/theory stuff--anything that would come up first when an agent in a new session starts to work in this
> session. "Constraint block", of course.
>
> Yup, let's go!

> **01:40:45Z** (mid-turn) Nuts, 2% until auto-compact

> **01:40:52Z** (mid-turn) Save it for persistence above all please

(He compacted the session at 01:43:07Z.)

> **01:44:47Z** Can you ground in the "constraint block" and what we were doing just before the compact

> **01:55:51Z** Good! Record the three messages and make those fixes, but don't jump into #4 just yet. I actually
> think it's better that you didn't read the ARCH document. It's good to get an independent understanding and use that
> to think through how it should be built and our work on auditing/correcting the general design ("the book") before
> we start to actually build. First, you get the idea of "computer vision" here? What it means specifically, and the
> general thrust of the thesis? Rather than reading the architecture document, I think it'd be better for you to
> lightly peruse the "what is an <object>" thesis. First, look at the global agent context file and read into the
> tooling that it discusses, read up on it, make sure you're familiar with what we have at our disposal. Then read and
> think it over, come back to me with what you understand about this. Also read the final turn of the "epistemology"
> conversation with Codex--just the prompt you sent and the response you got from Codex is sufficient. Then come back,
> and let's see what we do from there

("The three messages" are the first three above. "Those fixes" were two lines that predated his 01:33:48Z
rulings: CONSTRAINT_BLOCK's *Concurrence* under *Resolved*, and AGENTS law 2's "refused on disagreement". "#4" was
the lead's next step: begin the walk's Part 3 by reading KNEE_ARCHITECTURE's sections whole.)

## 2026-10-10 — the information section; the teacher; the story is the structure

> **00:01:30Z** One more thing I'd like you to read first--It's an update to the information theory articulation of
> the project thesis. Should really help think through the full design here:
> /Users/rohanvinaik/Projects/Kaggle_Killer/competitions/cell_tracking/docs/pipeline_thesis/paper/v7_parts/01_information.md

> **00:24:57Z** 1. The host data. That is *definitionally* what rates as correctness. The project is built on an
> assumption that people will be building ML solutions, so there is an absurd amount of data that is labeled in a way
> that is meant to be definitionally correct and unambiguous enough to allow for training of a machine learning model.
> Since this approach is deterministic and structural, the requirements for what makes a sufficient teacher are
> definitionally smaller and more ambiguous than what we are provided.
> 2. Yes, but you're leaning too hard into story understanding. This is a much simpler problem space. we have knee
> imaging data, we have a small set of posible diagnoses, and the things that enable a human expert to see the data
> and come to a conclusion--which is obviously possible, since "diagnosis" is literally the bar we are meant to hit,
> and diagnosis is literally a rules-driven conclusion based off structural reasoning on the condition and mechanics
> of human biology and imaging data like what we've been provided. The "story" here means "what elements of
> information provided, what combination of lossy lenses, actually tells us the structural reason why we can make a
> diagnosis?". Take the "thermometer" example from the thing I had you read. A thermometer is a simple tool. It
> measures temperature, and that's it. But we use it to measure the temperature of the mouth, or the inner ear, or the
> rectum, and calibrate the gradations on the thermometer to measure temperature, and use that as a proxy for core
> body temperature. THIS, in combination with other symptoms (runny nose, tiredness, sweating, chills, cough, sputum,
> whatever) allows a simple little tool to diagnose something as complex as the presence of viral or bacterial
> invaders that are disregulating the homeostasis of the patient. That's basically the thesis here. The "story" is the
> structure. The construction of meaning and understanding from simple, objective analyses.

(His 00:24:57Z answers are to the lead's two questions after reading v7 §1: who the teacher is for the knee, and
whether the knee has a story layer.)

## The engineering intent, in the founder's earlier words (2026-08-31, DETERMINISTIC_SICP §1.1)

> "I see this as a resource optimization problem. We want to optimize several 'independent' systems at the same
> time. Code should be small per function. Functions should be disentangled and independent. Code should be
> organized cleanly by intended function and type of operation. Computational efficiency should be optimized.
> Code should be written in the proper language and paradigm that appropriately executes the operation (e.g.
> Rust vs Python vs C++). There should be clean commenting and type-checking. Linters should have little to
> bite on."

> "…the job that is currently performed by experienced performance engineers (parallelization, JIT, one-hit,
> in-memory compute, cache optimization, etc). Right now in CS generally, and in SICP, these are idiomatic and
> vibe-y. But what we've built here is the computational and formal specification basis to make these concepts
> not vibes, but a directly optimizable set of decisions."

## How each message is honoured, and where

| the founder said | where the book carries it |
|---|---|
| the Kaggle key at the repo level | `AGENTS.md` → *Data, secrets, kernel*; chapter K03 (fetch) |
| questions resolved by building and observing | `CONSTRAINT_BLOCK.md` law 6; each chapter's *Open questions* names its measurement |
| retire the bad stubs | done in commit `358aa63` (consumers checked first) |
| read what the pointers point to | `provenance/build/reading_claude.md` §1 (each reference doc, read in full) |
| the best compute operation; JIT required; cache and memory | `AGENTS.md` → *Project overrides* 2–5; `THE_KNEE.md` §3; each chapter's *Implementation choice* section |
| the Mac Pro for heavy compute | `THE_KNEE.md` §4 and D7; chapters K01, K05, K07, K09, K23 (batch shards on `squishhub`) |
| the local Detective, by the same protocol | `AGENTS.md` → *Project overrides* 1; chapter K01 (identity and capabilities measured); chapter K02 (the `just detective` wrapper) |
| the book, one chapter per severable module | this directory |
| rules in a project-level CLAUDE.md | `CLAUDE.md` (imports `AGENTS.md`, per the house convention) |
| consult Codex on the exact design | `provenance/build/` |
| design fresh; reuse only when genuinely best | `CONSTRAINT_BLOCK.md` law 5; each chapter's *Prior art and reuse* section |
| cell tracking: a good start, not perfect | each reuse from it is argued in its chapter, never assumed |
| a different agent should agree from the chapters alone | `provenance/build/` — the fresh-reader check, run on the finished book |
| a small local model types under an Uroboros-style harness | the typist chapter, and its design read by Codex with the revised book |
| acceptance bars are discovery: a poor reading is a problem to solve, never a reason to discard or work around the design | `CONSTRAINT_BLOCK.md`; the chapter template's acceptance field |
| the rewrite grounded in KNEE_ARCHITECTURE, else `what_an_object_is`, else the manifest | `provenance/build/revision_1.md`: each finding with its grounding, read first-hand |
| derived records may enter git | `AGENTS.md` → *Project overrides* 7 |
| the lead does the reading; no sub-agents for grounding | `CLAUDE.md`; `AGENTS.md` → *How a session runs* |
| the developer and SICP tools read from their pointers; SquishOS as the home of the references | `CLAUDE.md`; chapter K02b's instruments table |
| language-specific modules (C/C++ for memory and cache, Rust for speed) designed in from the start, guided by the tools | chapter K02b (the compute design and the native layer); `THE_KNEE.md` §3.2 |
| Radon kept as an independent instrument, preferred to LintGate for complexity | K02 (dev tools), K02a (the fixture's gradient), K02b (the instruments table) |
| no operation exempt from engineering because it looks cheap; "suit and tie, not just "not naked"" | `CONSTRAINT_BLOCK.md` law 14; `AGENTS.md` law 8; K02b §1 and §3.4 |
| the lens principle is the rigid oracle and supersedes the architecture document | the twelve points at the head of `AGENTS.md`, `CONSTRAINT_BLOCK.md`, `THE_KNEE.md` §0 and THEORY; `provenance/theory/` (the readings, the Codex checks, the design walk) |
| the oracle front and center wherever a new session starts | the same heads; `CLAUDE.md`'s read-first line; ARCH's banner; the book's README |
| an independent understanding before the architecture: the tooling, the thesis, the last Codex exchange; ARCH not read for now | `CONSTRAINT_BLOCK.md` → *Next action* |
| the teacher is the host data, definitionally correct; a structural approach needs less of a teacher than is provided | `CONSTRAINT_BLOCK.md` → *Resolved* |
| the story is the structure: which combination of lossy lenses gives the structural reason a diagnosis can be made (the thermometer) | `CONSTRAINT_BLOCK.md` → *Next action*; `provenance/theory/thesis_reading_claude.md` §9 |
