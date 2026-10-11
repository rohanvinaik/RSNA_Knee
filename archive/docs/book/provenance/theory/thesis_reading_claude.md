# The \<object> thesis and the house tooling — the lead's independent reading (2026-10-03)

Written at the founder's word (01:55:51Z, verbatim in `../../FOUNDING_PROMPTS.md`): read the tooling the global agent
context discusses, lightly peruse *What an \<Object> Is*, read the last Codex exchange on the epistemology, and report
what "computer vision" means here and the thesis's thrust. KNEE_ARCHITECTURE was not read: "It's good to get an
independent understanding and use that to think through how it should be built and our work on auditing/correcting
the general design ("the book") before we start to actually build."

What was read: the global instructions and every routing-index document (`~/Projects/SquishOS/ops/agents/reference/`),
`docs/home/TOOLKIT.md`, `docs/spine/12-the-setup.md`, Detective's `AGENTS.md` and DETERMINISTIC_SICP's abstract and
§4–§10; the thesis (`cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md`, 2026-10-01) at its abstract, §1–§5,
§6.1–§6.3, §6.7, §7, §8.1, §9.1–§9.3, §10, §13 and §14; `codex_lens_principle_prompt4.md` and `…answer4.md`. Everything
below is my reading, for the founder to correct. Nothing in the design changes on it.

## 1. What "computer vision" means here

It is Minsky and Papert's sense: "a computer building and reasoning with descriptions of objects: their parts, their
relations and what they can do … It is not a mapping fitted from pixels to labels. A description can be checked
against what its objects must be, and corrected where it is wrong" (§1.1). That is possible because visual data is not
raw data: what a picture shows has physical presence, so "Most of the arrays a camera could record are pictures of
nothing that could exist, and a computer that knows the laws can rule them out before it looks" (§1.1).

The \<object> is a type, not a thing (the angle brackets are type notation, §1.2): what a general vision must
recapitulate, contiguous, closed, persistent, moved by physics and signaling by known laws. People reason on objects;
the computer reasons on \<objects>. "Vision" is then the interpretation built on measurement, as the founder put it
(23:50:20Z): "The reason why this is described as "computer vision" is because we assign an interpretation of what
these signals mean." The thesis's last paragraph: an \<object> "is not a label attached to pixels. It is a region the
structure can enclose, a light the optics explain, a profile the language writes, a case an expert confirmed, and a
track the laws carry through time" (§14).

## 2. The thrust

**One idea:** "A problem's structure carries information from outside any local question into it", and "the design
hands its computation to that structure" (§1.5, §14): seeing as a constraint problem, as in four-coloring by propagation
and Waltz's line labels (§2.5). **Its spirit is economy:** "It does the least computation that answers" (§14).

**Four hypotheses,** each resting on the one before, each with its bridge stated rather than assumed (§1.4):
- **H1, vision built from the laws** (§3–§5).
  - Deliberately lossy views. The squint: "reducing a signal on purpose, so that a categorical question resolves more
    cleanly and more cheaply" (§3).
  - Borders from the data's topology.
  - Elimination under law. What is knowably not an \<object> is removed. Each \<object> found is taken out whole, with
    the signal its physics says it spreads (the halo). The residual is read again: "what remains is the same kind of
    problem with added context" (the Wayfinder thesis, §4.6), and the lawful removal changed its meaning (the Monty
    Hall move).
- **H2, one exact language** (§6).
  - Every reading is a balanced-ternary digit against a fixed middle, in exactly orthogonal banks.
  - A silent bank, "no reading here", is kept apart from a digit at its middle.
  - Bundles are whole-number counts.
  - One cosine runs over only the banks a question reads, and an exact decode names a difference.
  - "No single number means anything" (§6.7).
- **H3, the bundles are K-lines and censors** (§7–§9).
  - An expert's confirmed case is a K-line's cue. Recall brings back the interpretation and the procedure it routes
    to: "a K-line remembers methods, not answers" (§7.2).
  - The case's −1 digits are censors.
  - A near miss is a confirmed failure that differs in one nameable way. It writes a censor, a split K-line, or
    nothing (§7.6).
  - Teaching happens once: hours, and dozens of examples.
- **H4, a society learns only the residue** (§10).
  - An agency is its question, its clean oracle, its cases and its measure.
  - Each agency decides or abstains.
  - Each is judged by its trajectory, identified / abstained / wrong per kind, never by one number. "Turning a wrong
    answer into an abstention is progress" (§10.4).

Throughout: law checks *support* a judgment; only an independent signal *establishes* one, and only for its own
question (§4.8, §10.5). Learning is the classical kind: "a departure from what was expected, kept with how it was off,
in what context and about which role of which typed object" (§1.3, §7.1); nothing is a fitted weight.

**Where it holds and how it fails:**
- A precondition of five clauses (§1.3): the laws can be stated; the state is discrete, with one true answer; each
  lossy view can be read against one law; each learner has a clean signal; the laws can be checked on the output.
- A nine-step recipe for a new domain (§13.1).
- Six measurable findings that would falsify it (§13.3).

## 3. The thesis read against the rigid oracle

The lens principle reads as this thesis's epistemology stated as rules; nearly every point has a passage behind it.
- **Points 1–2.** A lens "measures one thing and knows no question. No answer is built into it: only the step that
  reads it takes its value as evidence for or against anything" (§3.2). The composite "never decides alone: it points"
  (§3.3), and the priors "point and never decide alone" (§13.1).
- **Point 9.** The senior filter of the black is "narrow and knowably correct: it does not fire wherever light is
  faint, but where it fires it is right, and it decides alone" (§4.2). Specks narrower than 2 µm go "since nothing that
  small is a nucleus" (§4.3).
- **Points 4 and 5.**
  - The call table (§7.3) is the third bucket exactly: not-cell-not-noise writes noise −1, cell 0, and "One symbol per
    call cannot say "against noise, silent on cell"".
  - The thesis also keeps the two senses of the digit apart. A digit 0 is a reading at its middle; a call's 0 is
    silence: "the notation is shared, the meaning is not".
- **Points 7 and 8** (§8.1). "One cell: at least two families for it, and none against" is a downward-looking contract:
  one family against makes the assignment fail. "Readings of one light are not independent, so they count by these four
  families" groups correlated readings rather than discarding them.
- **Point 10.** "There is no noise": "a removal is a decision by a reading entitled to make it, kept as a record, never
  a discard … a disagreement between correct readings is information" (§4.2).
- **Point 11.** "Every step obeys decide or abstain … an answer is given only under proof, by its contract, and
  principled abstention is one of the strengths of a law-based design" (§4.8).
- **Point 6.** Whether a candidate is one nucleus, several, or light that belongs to no cell "is a judgment of meaning,
  and its oracle is an expert's visual reasoning" (§8);
  "the oracle behind every teaching signal is in the end a human expert" (§10.1).

**Two passages keep the form his 01:33:48Z rulings relaxed** (a textual comparison, for his ruling). They matter
because revision 1 grounded the book in the thesis where ARCH was under-specified (16:29:22Z).
- "Truth among them is assigned by concurrence and refused on disagreement" (§1.4, H4; again in §14). §4.4 says it of
  the lenses: "assigned where independent readings agree, refused where they disagree". Recall's rule is "Two or more
  are a disagreement, kept, and never broken by order, averaging or the strongest voice" (§10.2). His ruling: "not
  wrong as a principle, it is wrong as a law"; "a majority *can* be a sufficient contract".
- "the independence of views is measured before their agreement counts" (§6.2; also §6.7). His ruling: "correlation
  isn't damning in and of itself". §8.1's families already count correlated readings as one, not none.

## 4. The tooling at our disposal

Each instrument licenses one kind of claim, and no more (`context-handling.md`).

| need | instruments |
|---|---|
| reading code and meaning | Serena (`find_referencing_symbols` before every edit), `aider-map`, ast-grep, semgrep and AST queries, symbex, ctags, mdq, QMD, repomix and ttok, `git log -L`/`-S`, difftastic. A hit locates; it never explains |
| types and contracts | `ty` (advisory) with Pyright beside it; CrossHair and icontract; Import Linter for layers; deptry for dependencies |
| behaviour | the local Detective, run from the project's venv with `PYTHONPATH` set to the checkouts, on extracted pure decisions returning named codes (the `just detective` wrapper that AGENTS.md names is K02's, and no `justfile` exists yet); Wesker, with mutmut beside it; Hypothesis for the laws of an abstraction; intent tests beside each characterization |
| organization and performance | Hamilton (the run as a graph of named values); VizTracer, with cProfile for threads; Scalene, memray, py-spy, pyinstrument, line_profiler; Numba as a probe, `cython -a`, Codeflash; budget claims as Detective's paired opcode counts, with pyperf and asv as complements; structlog and OpenTelemetry for a run's record |
| native code | Rust (rustup, clippy, PyO3 + maturin); C/C++ (clang, lldb, clang-tidy, CMake + Ninja, AddressSanitizer and UBSan, Compiler Explorer) |
| the SICP and classical-AI workshop | Racket `#lang sicp`, SWI-Prolog, SymPy, NetworkX, Lark, Matplotlib; Regenesis and Wayfinder as MCP servers |
| gates and supply chain | ruff (check and format), `ty`, pylint as a Sonar approximation, pip-audit over the lock with all extras and groups, zizmor, a secret scan, sp-repo-review, scorecard |
| second readers | Codex (model-only, GPT-6-Astra at medium) and Antigravity (`agy`, Gemini 3.1 Pro or GPT-OSS), each one voice; `consult-budget` |
| the machine | osquery, psutil, Czkawka, watchmedo and the native instruments; the Mac Pro only through `squishos-compute`; local models only through `squishos-harness` |

**The same epistemology runs through the tools.** This is my observation.
- Detective's protocol: "A refusal is a VERDICT, not a bug report."
- DETERMINISTIC_SICP's controller reads banks by interference: SILENT, CONSTRUCTIVE, DESTRUCTIVE or AMBIGUOUS. There
  "one confident opposition vetoes a pile of weak supports"; banks "never fuse or average"; "an unmeasured bank votes
  0" (§4.1, §5.1); and "Interference, never weighted sums" is a law (§9).
- That is the downward-looking committee in the house's own tooling.

**Mappings I would expect for the build** (inference, to be argued per chapter):
- decide-or-abstain contracts (the commit, recall, a near miss's three outcomes) as Detective-pinned pure decisions
  returning named codes;
- the language's laws (orthogonal rows, exact decode, bundling as whole-number counts) as Hypothesis properties;
- "a lens knows no question" as an Import Linter contract, with no lens module importing an agency;
- the bundling and cosine loops in Numba, and the case scan in Rust, as the book already plans.

## 5. The last Codex exchange

The question (`codex_lens_principle_prompt4.md`): is the six-point epistemology rigorously clear, and is it his? Codex
(`codex_lens_principle_answer4.md`): "The core epistemology is clear, and the reading substantially matches his stated
position. It is not yet a complete formal specification", citing his "what we have to establish" line. Its
qualifications:
- keep the third bucket's name separate from its warrant;
- "image, not disease" is shorthand that must keep his distinction;
- the downward look is faithful, but "near-miss learning" is no formal label for every majority-with-dissent ruling,
  and "not wrong as a principle" endorses no particular refusal rule;
- the Pearson identity was my addition; his word is "compatible";
- the strict-exclusion gate's criteria remain to be established.

Read beside the thesis, the first qualification is the thesis's own call table: the warrant is the digit pair, and the
name only labels it.

## 6. What it raises for the knee (questions, mine)

1. **The \<object> and the categories.** §13.2's MRI row gives "An organ; a lesion" as the \<object>. Its laws are that
   "A tissue's brightness is set by its magnetic relaxation under the sequence" and that "anatomy is contiguous from
   slice to slice". Its lenses are "One per sequence", and its teaching is "A radiologist's calls". Under his ruling,
   I read it this way:
   - the knee's \<objects> are its structures;
   - what the structure resolves are definable categories of image within and around them;
   - the competition's twelve findings are meanings he ascribes to those categories, never categories the structure
     assigns.

   Is that right?
2. **Clean signals (precondition, clause 4).** This looks like the clause the knee must settle first. For cells, an
   expert's calls on candidates taught the identity agency in a few hours. Here the competition's literal data gives
   study-level labels and the radiology reports. Who calls candidates in the knee, and on what?

## 7. Proposed next step

Work §13.1's nine-step recipe for the knee from this reading, each step a proposal for his ruling. Then hold the book's
chapters against it. KNEE_ARCHITECTURE stays unread until he says otherwise.

## 8. The v7 information section (read 2026-10-10)

At the founder's word (2026-10-10 00:01:30Z): "It's an update to the information theory articulation of the project
thesis. Should really help think through the full design here." The section was read whole:
`cell_tracking/docs/pipeline_thesis/paper/v7_parts/01_information.md`, 1,616 lines.

**What it is:** one story in three operations, each a question asked of any reading.
- Acquiring (§1.1–§1.4): what has been acquired?
- Deriving consequences (§1.5–§1.9): what follows?
- Authorizing assertions (§1.10–§1.14): what may be asserted?
- §1.15 gives the substrate the three share.

An abstention "names what would supply an answer: the next acquisition … or the next call a teacher must make" (§1.14),
so the loop closes.

**What it settles from §3 and §5 of this reading:**
1. **The two passages in the form of law.**
   - §1.11 says: "A committee of views decides positively, negatively, ambiguously, or by a majority with its dissent
     recorded, and for each ruling it needs a contract, written before it sits. A majority can be such a contract: a
     rule for when to rule, never what makes a ruling correct. The contract looks downward."
   - The commit's refusal on disagreement, the word "one cell", and recall are three such contracts.
   - So refusal is a contract chosen for one step, not a law of the society.
2. **Independence.**
   - The chain rule "needs no assumption of independence": a second view never lowers what is known (§1.3). How
     independent the views are limits how much they add (§1.6).
   - "A family is the readings of one source. They are not independent of one another, so they count once, and no
     evidence is counted twice" (§1.11).
   - Between views that agree nineteen times in twenty, a disagreement carries about 4.32 bits and an agreement 0.074
     (§1.6).
3. **The strict-exclusion gate.**
   - The criterion: "A lens takes the same standing only where the structure gives it: where a law of the domain, not
     a run of past successes, says on which side the lens cannot err" (§1.11).
   - A wide lens clears by exclusion (SnNout).
   - A narrow lens settles where it speaks (SpPin, "first among equals").
   - Seniority is "one of authority, not of strength".
   - Even then the standing is a warrant, open to a near miss.
4. **Warrant.**
   - "What a lens may assert is fixed by where the structure places it. We call this its warrant" (§1.10).
   - "Information is not warrant."
   - A warrant is strict or directional, and nonmonotonic.
5. **Meaning:** "A person with fluid intelligence does not build or invent that structure. Such a person resolves it,
   by understanding the domain, and defines it so that a system can use it" (§1.1).
6. **"Ledger"** is the thesis's own word (§1.6).

**One change from the 2026-10-01 version, which the book must be checked against: the static middle.**
- Then: "set once, at the metric's terciles over the movies the system is taught on … It never moves per movie"
  (§6.2).
- Now: "read once for each movie, cheaply, off the movie at its start, and held through the run" (v7 §1.6).
- Wherever the book writes the edges of a digit, it was grounded in the earlier text.

**How it bears on the knee** (my reading, proposals only):
- **Acquiring.**
  - A study's series are views at right angles, the front and profile photographs of §1.3: "exact about what it
    shows and silent about the rest". By the chain rule each adds what the others cannot, with no independence
    assumed, so no series is judged by how much of the knee it shows alone.
  - A lens is never wrong about what it measures; if it reports anything else, "the fault is in its code" (§1.1). So
    each lens is a defined, pinned pure function.
  - Space can play time's part ("Time is not a privileged dimension. It is one more lens on the field", §1.4).
    Contiguity from slice to slice is a two-sided prior like the sandwich, never a sighting. A false reading holds over
    k neighboring slices with probability p^k only where its occurrences on neighboring slices are independent, and
    that must be measured.
- **Deriving.**
  - The population of normal knees in one frame is side information (§1.5). It is the reference of §1.8, "a
    statistical superposition … so that subtracting the reference left only what was particular". The study's
    difference from it is the signal.
  - The thermometer (§1.10) marks what that difference alone may not say: a deviation is a temperature, and what a
    category means is a fever.
  - Each structure resolved goes out with what its laws say it causes, and the residual is read again (§1.8–§1.9, the
    rib and the nodule). Which structures come out first, and what each carries out with it, are design questions.
  - The edema of §1.2 is the knee's own example: "two relevances of the same thing", evidence for one question and
    signal to take out of another's view, and never evidence against.
  - A conjunction is a product term: "a bundle is not an OR, and a binding is not an AND", and "An interaction between
    banks … needs a code for the combination itself" (§1.6). Each conjunction the knee's truth tables need gets a code
    of its own.
  - "The substrate is therefore an efficiency layer: a cheap, exact filter, not a store of values" (§1.6). Values are
    kept beside the digits, and the arithmetic runs on the values.
- **Authorizing.**
  - A law decides each lens's warrant (strict or directional) and its standing (wide, narrow or senior), never a track
    record. The walk's classes (T1, C, evidence) are this vocabulary.
  - Each ruling's contract is written before it sits, and it names what defeats an assignment.
  - The three zeros (§1.12): a series that cannot see a place writes a silent bank. That is neither a digit 0 nor
    evidence against.
  - The guard and the completeness map (§1.14) frame the teaching question: structure, corpus, teacher, remainder.
    A call teaches only if its provenance is independent of the memory.
  - An abstention names the next acquisition (which series or view would settle it) or the next call.

**Questions (mine):**
1. **The teacher term.** In the completeness map, who is the teacher T for the knee?
   - The founder's calls on candidates?
   - The hosts' study-level labels?
   - The reports?
   - Each for its own agency?

   All three have provenance outside the memory, but they answer questions at different scales: a place, a study.
2. **A story layer.** §1.15 marks a structured problem by "a causally one-way story that explains it". A study has no
   movie. Does it have a story, the mechanism of an injury, whose chapters the findings are (the kind of reading
   Regenesis does)? This is a question about structure, which is his to resolve and define.

**Proposed next step,** unchanged: work §13.1's recipe for the knee, now through the three operations, each step a
proposal for his ruling. Then hold the book against it, with the static middle among the first checks.

## 9. His answers (2026-10-10 00:24:57Z, verbatim in `../../FOUNDING_PROMPTS.md`), and my restatement

**The teacher is the host data.** "That is *definitionally* what rates as correctness."
- The data was labeled for builders of ML: "meant to be definitionally correct and unambiguous enough to allow for
  training of a machine learning model".
- "the requirements for what makes a sufficient teacher are definitionally smaller and more ambiguous than what we are
  provided."
- So the completeness map's teacher T is the host data. Its provenance is outside our memory, so under the guard it
  teaches, and it gives more than a structural design needs.

**The story is the structure, not a narrative layer.** "you're leaning too hard into story understanding. This is a
much simpler problem space."
- The question is "what elements of information provided, what combination of lossy lenses, actually tells us the
  structural reason why we can make a diagnosis?"
- Diagnosis "is literally the bar we are meant to hit". It is "a rules-driven conclusion based off structural reasoning
  on the condition and mechanics of human biology and imaging data like what we've been provided".
- An expert reaches it from such images, so the information is there.

**The thermometer, in the knee's terms** (my restatement, for his check):
- **The thermometer.** It measures temperature and nothing else. Placed at a site, with its gradations calibrated, it is
  a proxy for core temperature. Read with the other symptoms, it lets "a simple little tool" diagnose an infection.
- **Each lens in the knee is such a thermometer: one simple, objective reading.**
  - Its site is a place in the registered frame: which structure, which part of it, in which series.
  - Its calibration is the population of normal knees at that place, in that sequence.
  - A deviation at a registered site is therefore the proxy: a temperature, never yet a fever.
- **A diagnosis is a conjunction of such readings,** read through anatomy, MR physics and the mechanics of injury, by
  the rules a radiologist uses.
  - Each such conjunction is a path of the encoded truth table.
  - It is strict where a law makes it so, and directional otherwise.
  - Where no path warrants, the structure abstains.
- **Categories and diagnoses.** The categories of image (01:33:48Z) are what the readings resolve into, and the
  diagnosis is the structure's conclusion from them. The rules are the domain's, and he resolves and defines them
  (v7 §1.1).

**The form of the work, finding by finding:**
1. its definition, in the hosts' literal words (admissible as fact);
2. the structural reason it can be diagnosed: the laws of anatomy, MR physics and the mechanics of injury that make it
   visible;
3. its thermometers: the lenses, each one objective reading at a registered site, calibrated against the population;
4. its paths: which combinations assign it, which reading or law rejects it strictly, and where it abstains;
5. what the host labels confirm, and the near misses they expose.

Each is a proposal for his ruling. One finding goes first, as a worked example to fix the form with him. The rest
follow, and then the book is held against them.
