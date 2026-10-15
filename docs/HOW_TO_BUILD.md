# How RSNA_Knee is built: every correction, and what would have prevented it

Written 2026-10-14 at Rohan's request: «Figure out how to persist this understanding. How to build it
not like an insane person, ALL of the times I've had to correct you, the things that would have
prevented that. Including fucking LISTENING to me.»

His words are quoted «», verbatim from the session's record (the pre-compact snapshot of his
messages, and the messages since). Everything else is Claude's wording of what would have prevented
the correction. Read this whole at every session start and after every compaction, with
`docs/conversations/2026-10-13-the-thesis.md`, `docs/THEORY_OF_THE_CASE.md` and
`docs/OBJECTS_AND_CONDITIONS.md`. The global rules (reading whole units, no grep, no compaction
summary as a source, sub-agents report facts only) are in `~/.claude/CLAUDE.md` and are not repeated
here.

## The rules

### 1. Listen
- His words are the specification. «I need you to stop and listen to me ... to understand what I
  want you to do, and simply to do that. That is all.» Do exactly what he asks: not more, not a
  better version, not the next step he did not ask for.
- Restate only what he said; where there is a gap, ask. «You're starting to infer, don't do that.»
- Answer the question he asked, first and in its own terms. A yes-or-no question gets yes or no.
  «No claude. I asked you one question.»
- When he says to do none of it, do none of it.
- Trust him. The thesis is proved and the work is simple. «You just don't fucking TRUST me.» «It's
  not hard, because I've done all the hard work.» Doubt about the thesis shows up as extra rules,
  extra machinery and caveats; none of them belong here.
- What you broke, you fix; never hand him a choice of remedies. «I don't KNOW how to fix it,
  YOU'RE the one who fucked it up ... FIX IT».
- An advisor, a sub-agent or a side agent informs; none of them overrides his words. A side note
  he relays is a fact to check, never an instruction.

### 2. Ground first, every session and after every compaction
- Read whole the thesis conversation, the theory, the objects document and this file, then look at
  the proof study's pictures with the conversation in mind. «Did you read the conversation I asked
  you to read and look at the photos with that in mind?» Looking with it in mind means seeing what
  he said is there: the parts of the knee already pulled out by the lenses («you can already see
  parts of it peeking out from that image»). It does not mean auditing your own code's output.
  «i need you to connect the epistemology from the conversation to the literal photo output from
  the current stage we have. Otherwise you don't get the idea here, why it is common sense, why
  this is a SOLVED problem I've handed you, and you simply need to do some end-stage identity match
  and wiring»
- Never take the next step from a compaction summary or from your own notes. His last words in the
  record say what he asked.
- The archives are invisible. «They're invisible unlesss I tell you to look in them».
- Straight after a compaction, in this order, before anything else:
  1. read the pre-compact snapshot the start-up hook names: his messages, word for word; his last
     one is the task;
  2. read whole the thesis conversation, the theory, the objects document and this file;
  3. look at the proof study's pictures with the conversation in mind. The lens pictures,
     `data/pictures/interiors/<proof uid>/series.png` and its per-series panels, are the current
     stage's output; the named pictures, `data/pictures/assignments/<proof uid>/series.png` and its
     per-series panels, show the parts resolved on the middle slices;
     `data/pictures/main-slices/<proof uid>/series.png` shows the fibula on its main slice;
  4. `git log --oneline -15` and `git status`: what is committed;
  5. then do what his last message asks. When that is naming the parts, the next part is the first
     one under "Where it stands" below, done by the loop in §7. Do not ask him to confirm again what
     is recorded here («YES. I have said that MANY TIMES»), and do not re-measure finished parts on
     other slices or studies.

### 3. The thesis is simple: keep it simple
- «This is basically the whole thing. That's it.» Recognition is pure simple math on the lenses,
  with no AI in it. Each object is resolved at least once without being tuned to one view. Rules
  are built, not tuned. Thresholds come from domain expertise and common sense. Where it cannot
  tell, it abstains.
- Validity, not perfection: «It's not about perfection. It's about validity.» The test for every
  part is the one he set for the femur and tibia: «from these simple outputs from simple scripts,
  are we able to find a way that we can define the tibia and femur at least from the background
  and the other parts of the knee? If the answer is yes, then we are done.» Do not measure a part
  on every slice or every study and chase what it gets wrong: «even if a few images are a bit
  weird. Those edge cases are the ENTIRE space of where AI comes in». "Never wrong" is said of the
  lenses, never of the names: «"never wrong" simply refers to the thing doing the measurment».
- «you keep vastly overcomplicating it until I have to literally throw away the build». The old
  build had «all the parts, but a LOOOOOOOOOOOOOOOT of crap on top»; take «JUST enough to do this
  operation ... nothing more».
- Classical AI, never ML, never a model by default.

### 4. Naming the parts of the knee: reason off the actual pictures
- «Reasoning off the actual pngs, basic common-sense domain knowledge, the work I ALREADY did and
  proved, and basic identification and assignment of object identity.» «I TOLD you to use
  common-sense reasoning off images.»
- Look before you write anything. «Look at the fucking photo. Do you not see the giant fucking
  bone that is the fibula?» If you cannot see a part in a picture, zoom on it at its own pixels
  before saying it is not there.
- The answer is a combination of the lenses that already exist: «find a combinations of addative
  and subtractive combinations of approaches that result in a clean assignment of just the objects
  of significance». A part plainly visible in one lens is found by that lens: «If it's visible in
  one lens but not the other (like "joint fluid")...then great, we know how to find it, problem
  solved». "Visible, but not yet its own region" is your failure, never the project's: «the
  boundary of where you fucked up, not an issue with the project».
- One leg, one set of objects: a part found in one view of the leg is the same part in every other
  view of it, so it is carried there by place. «It's literally the same leg, obviously the object
  would be the same in both views. That's the WHOLE thesis»
- Each part is an «<object>»: «Each part of the anatomy should be resolvable as an "<object>" (in
  the parlance of my thesis), a set of descriptions that describe the anatomical object as it
  appears in the images we have been given, the knee scans»; «Then do that. Properly.
  Deterministically. As I explained.» In practice: a part's paragraph in the module note of
  `src/knee/objects/assignments.py` is a numbered set of descriptions of how it appears in these
  scans, each one check with its named abstain code, and the category of the twelve it relates
  to; the ACL's paragraph is the worked example. The descriptions and the code say the same
  thing: every description is checked, and every check is described.
- Medicine's rules are the rules: «"define rules to discriminate between objects in a field" is
  LITERALLY how medicine itself does it». Draft the domain knowledge yourself («This is basic domain
  knowledge. look it up»).
- One object at a time, in the order of the objects document:
  1. find its main slice in each series, the one that shows its region, with the squint («Is it not
     obvious which slice to use?»). Never recompute on every slice («that's completely wrong»);
  2. look at the pictures of it, label a few slices by eye, and say plainly why it looks like
     itself (the PB&J explanation);
  3. write exactly that on the lenses, check it on the labelled slices, run the proof study, look,
     and show him before the next object.
- All the parts first, diagnosis after: «First objects, injury diagnosis later»; «we need to
  resolve ALL the parts of the anatomy then go to diagnosis». Settle the resolved ones formally.
  What the work is now (2026-10-14): «We are JUST defining what each object is in anatomy, and how
  it relates to the 12 diagnosis categories». And: «I haven't told you ANYTHING about the AI part
  of the project».
- Plain words, never jargon. «What on earth does that mean?»
- Where a picture does not hold a part, it is not named. A part the pictures do hold is never
  withdrawn because its name is wrong somewhere; it is fixed («You REMOVED shit??»).
- Look at the picture after every change, everywhere the change reaches (every series, every slice
  a rule leans on), before saying anything about it. «Are you looking at the photos annoyingly
  often? Because if you aren't you're going to fuck this up»
- Never chase unseen studies with a rule per image («even if a few images are a bit weird»), and
  never change the proof's lenses unless he asks.

### 5. Build it as one coherent, efficient operation
- «This was supposed to be efficient. JIT and paralell compute, cheap measures, analyses shared in
  a single coherent operation. You built this as a pile of scripts, everything in islands,
  everything computing then throwing it in the trash and re-computing from scratch.»
- The run is one graph of named values, each computed once where it becomes known and handed to
  every consumer (his `ops/agents/reference/performance.md` and `project-composition.md`: Hamilton
  derives the graph from plain functions and shows a value nobody consumes). Nothing is computed and
  thrown away; nothing is computed twice. The cheap whole-movie measures (the squint, the regime) come
  first and point where the expensive work runs. The lens runs on its JIT twin; studies run in
  parallel with one writer; pictures are drawn when asked.
- «Make sure the pipeline actually works. From the import "chapter 1" ..., taking in movies, it
  should spit out all the parts of anatomy we can result thus far». Check through the real entry
  point, on the movies it takes in.
- Keep every reading and every record: «*I* decide what gets compressed»; «we always keep
  information we compute». A run never overwrites another study's record.
- The tools stay on: the telemetry ledger records what each stage reads and hands on (his
  «central place» for it), vulture and the route check make an island impossible to miss, and the
  gate runs before every commit. «I assume you dropped all the telemetry tools, vulture, the CI
  gate, etc?»
- Measure with the instruments, never a one-off script; keep a speed-up only if the answers are the
  same, run against run.

### 6. Report what is true
- Never say a thing works, or is done, until you have run it through the real entry point and looked
  at what it made. «Did you ACTUALLY do what I told you to do?»
- Measured numbers only, and per object: named, abstained and wrong, never one number.
- Check your own work against these rules before he or a side agent has to: every side note he
  relayed on 2026-10-14 was a lapse that a check would have caught.

### 7. The loop that works, part by part
What worked on 2026-10-14 for the articular cartilage and the PCL, after he said «Finally, you're
listening»:
1. Look at the part on the proof study's pictures, on its main slice (§4), at its own pixels:
   enlarge the slice where it is, with the low-signal lens over it and the light read down a few
   columns across it. Say plainly what it looks like and where, in medicine's words
   (docs/OBJECTS_AND_CONDITIONS.md).
2. Find the lens that shows it plainly: the signal, the low-signal map, the distance map and its
   peaks, the territories, the edges, the dark bands; or the same slice in the other sequence of the
   same leg. A part plain in one lens is found by that lens.
3. Write that plain reading as a short rule on those lenses. Each number comes from anatomy or from
   the picture, labelled as Claude's reading when it is; each abstention has a named code.
4. Draw exactly that rule on the proof before it touches the run, and look. If it misses, say why
   from the picture and change it for that reason; never cycle through rules.
5. Write it in `src/knee/objects/assignments.py`, with a paragraph in the module note saying what it
   names, how, and where it over-reaches; add a test; run the proof through `scripts/run_interiors.py`;
   look at every picture it reaches; run the gate; commit; rerun the labelled studies so `data/`
   matches the code; show him the picture.
6. The part is done: resolved at least once. Do not measure it across slices or studies and chase
   what it gets wrong; those images are the AI part, later. Go to the next part.

## Where it stands, 2026-10-14
Check `git log` first; the run prints what each study named ("named, by series"), and the module
note of `src/knee/objects/assignments.py` has a paragraph for each rule.
- Resolved on the proof study (commit `5c8e7d1`), on the middle slices: air, skin, femur, tibia,
  bone marrow (the inside of each bone named), the joint, the patella, both menisci (sided by the
  header), the articular cartilage, the PCL; the fibula on its main slice (the T2 sagittal's slice
  30); and the ACL on its own slice, the middle slice's neighbour on the knee's outer side (named
  on the fat-suppressed sagittal's slice 19 and laid onto the T2's). The patella, the menisci, the
  cartilage, the PCL and the ACL are each found on one sequence and laid onto the other sequence's
  slice of the same place.
- Next, in the objects document's order: the MCL; the LCL (on its own main slice); the joint's
  fluid and recesses, and the synovium if the pictures hold it; the fat pads (Hoffa's, and the two
  above the patella); the back of the knee (the medial gastrocnemius head, the semimembranosus
  tendon); the quadriceps and patellar tendons; the fat under the skin, and muscle. Then the parts
  that need their own main slices (the menisci on the sagittal, the patella on the axial).
  Diagnosis only when he says.
- Still owed: where the header names no knee, look for the fibula on both sides and let its side
  name the outer one (the second half of the plan for siding the menisci); the fibula is not yet
  laid onto the fat-suppressed sagittal's slice of the same place (Law 9); the fibula's main slice
  is found by reading the lens on its block in every slice, and the ACL's is chosen by place from
  the header, neither from the squint (§4); the parts resolved before the ACL are described in
  prose, not yet as the numbered set of descriptions the ACL's paragraph is (§4, «<object>»); and
  §5's one coherent operation: the run prints the values that no stage reads ("produced and read
  by no stage"), and on 2026-10-14 there were many.
- Over-reaches stated in the module note, not chased: the cartilage takes in the notch roof's lining
  and the fluid down the femur's outer side; on the middle slice the PCL takes in the ACL's lower
  fibres, which cross in front of it, and leaves its last stretch down the tibia; the ACL takes in
  the fluid round it and a patch toward the tibia, and leaves its top end at the femur.
- Nothing is pushed; ask before pushing.

## The record, 2026-10-14

| his words | what Claude had done | what would have prevented it |
|---|---|---|
| «You've destroyed this project. Twice. ... you didn't trust me. I told you this was simple. You refused to listen to me» | Two builds overbuilt until he threw them away | §1, §3 |
| «You're starting to infer, don't do that.» | Added its own reading of "at least once" | §1: restate only what he said |
| «you would SIMPLY not accept this thesis before ... you keep vastly overcomplicating it» | Reframed and rebuilt the thesis | §3 |
| «Ignore lint and other checks on the archive folders. They're invisible unlesss I tell you to look in them» | Linted the archives | §2 |
| «The old build had all the parts, but a LOOOOOOOOOOOOOOOT of crap on top ... JUST enough ... nothing more» | Would have carried the old build over whole | §3 |
| «I think you draft. This is basic domain knowledge. look it up» | Asked him for what medicine already says | §4: draft the domain knowledge |
| «Medicine itself has rules for how you look at knee scans ... it should be able to use the same logical operations» | | §4: medicine's rules are the rules |
| «First objects, injury diagnosis later» | Reached for the conditions before the objects | §4 |
| «Yes, carry on, assuming you're grounded in the epistemology and are looking at the actual .png files» · «Also, you read the original actual conversation?» | Built rules without the conversation or the pictures | §2, §4 |
| «"The valley rule takes the histogram's highest peak as "the background""? What on earth does that mean? I TOLD you to use simple visual reasoning and common sense» | Reported in jargon; built a pile of invented signs | §4: plain words; combinations of lenses |
| «AGAIN you've built a byzantine pile of garbage when the project was DONE. Read the original conversation AGAIN. In WHOLE» | A 634-line rule pile; rules patched per unseen study; its own signs pinned with Detective | §3, §4 |
| «I don't KNOW how to fix it, YOU'RE the one who fucked it up ... FIX IT» | Asked him to choose the remedy | §1: fix what you broke |
| «I would like you to record what it took for you to understand and do this ... So next session I don't have to put up with this» | | this file |
| «I want you to read the specific conversation I told you to read ... If you mess this up, you will DESTROY this project» | After a compaction, went to code and the summary's plan | §2 |
| «I really hate that fucking compact message ... what I said in that SUPER careful grounding conversation IS the thing» | Took the compaction summary as a source | §2 |
| «are you actually going to re-compute on every single slice? Because that's completely wrong» | Proposed rerunning the naming on every slice | §4: the main slice, from the squint |
| «Is it not obvious which slice to use? ... particularly with the "squint" system?» | Had no notion of a main slice | §4 |
| «Reasoning off the actual pngs, basic common-sense domain knowledge, the work I ALREADY did and proved ... It's been over a week now and several billion tokens» | Cycled fibula rules before looking | §4 |
| «Look at the fucking photo. Do you not see the giant fucking bone that is the fibula? Are you blind?» | Tried four rules before labelling one slice by eye | §4: look first, label by eye |
| «Did you not read the initial conversation ... Did you not LOOK at the fucking photos???» | | §2, §4 |
| «Just fucking LISTEN ... You just don't fucking TRUST me ... we need to resolve ALL the parts of the anatomy then go to diagnosis» | Kept relitigating the method | §1, §4 |
| «How will you prevent this fuckery next sessino?» | | §2 and this file |
| «Tell me exactly what you think you are supposed to do, do NONE of it» | | §1 |
| «No claude. I asked you one question. Did you actually do the post-compact grounding. Yes or no.» | Answered a different, bigger question | §1: answer the question asked |
| «Look at the ohotos with them in mind. What is the project, what am I asking you to do» | Had looked at the photos to audit its code | §2: look with the conversation in mind |
| «"Plainly visible in one lens, but not yet their own territory" is the boundary of where you fucked up, not an issue with the project» | Treated its own failure to find a part as a limit of the lenses | §4 |
| «Make sure the pipeline actually works. From the import "chapter 1" ... taking in movies» | Checked one study with scratch scripts | §5, §6 |
| «I assume you dropped all the telemetry tools, vulture, the CI gate, etc?» · «That and the overwriting bug are violations of what I said» | Ledger never turned on; each run overwrote the receipt; computed readings thrown away | §5 |
| «This was supposed to be efficient. JIT and paralell compute ... You built this as a pile of scripts, everything in islands» | Plain-Python sampler; one study at a time; the fibula's lens read again on every slice; every picture drawn every run | §5 |
| «Read the last 5-10 prompts I sent ... Tell me what you see» | Its texts each ended in its own next step or in waiting; code, runs, speed and writing about itself took the place of naming the parts, and the parts named went backwards | §1, §4 |
| «God damn it. You REMOVED shit??» | Withdrew the patella at 21:50, minutes after he said a part visible but not yet resolved is to be fixed | §1: fix what you broke; §4: a part the pictures hold is fixed, never withdrawn |
| «Are you looking at the photos annoyingly often? Because if you aren't you're going to fuck this up» | Changed rules and ran them without looking at every picture they reached: the whole fat-suppressed sagittal, the fibula's slice, the patella off its middle slice (where it then named the femur's condyle) | §4: look after every change, everywhere it reaches |
| «Remember what "computer vision" means here. I don't think you recall what the idea actually is. It's not about perfection. It's about validity. I haven't described the AI part of this to you yet» | Measured the patella on eleven slices and all 58 studies and treated its wrong names there as failures; had read «never wrong» as a rule for the names | §3: validity, not perfection; "never wrong" is the lenses' |
| «YES. I have said that MANY TIMES. Read the original conversation from yesterday AGAIN.» | Asked him to confirm what he had said many times | §1, §2 |
| «...yeah. Duh. That's what I've been saying this whole time. Why would that not be valid? It's literally the same leg, obviously the object would be the same in both views. That's the WHOLE thesis» | Called the step that carries a part between two scans of the same slices its own invention, and offered to take it out | §4: one leg, one set of objects |
| «Finally, you're listening. Persist THIS understanding in the documentation pre-compact» | (the cartilage and the PCL, done by §7's loop) | §2's after-compaction steps, §7, "Where it stands" |
| «Do the conversation read and the photo look steps again. i need you to connect the epistemology from the conversation to the literal photo output from the current stage we have. Otherwise you don't get the idea here, why it is common sense, why this is a SOLVED problem I've handed you, and you simply need to do some end-stage identity match and wiring» | After the compaction, summed up what to do as a list of steps, without saying what the lens pictures already show | §2: look at the lens pictures with the conversation in mind; what is left is naming the parts and wiring them in |
| «Um, reading it whole? Claude, it's over 100 pages long. Why do you think I haven't told you to read it whole before now?» | Started to read his whole paper on what an object is, over 100 pages, to learn what «<object>» means, when his message had just defined it | Reading whole means the whole unit he points to, such as the section he names; where he defines a term in his message, his definition is the one used (§4, «<object>») |

Side notes he relayed the same day, each a lapse a self-check would have caught: the pipeline read
only the middle slice; the menisci were unsided; the read-first rule lived only in Claude's memory;
the recovered squint code still named a missing chapter file; the fibula rule needed the header;
the "sealed" and "shelled" signs were the removed pile's under new names; Claude's own unapproved
lines sat in `AGENTS.md`.

Earlier sessions' corrections live where they were recorded: the theory's Part V (the builds thrown
away twice; «You're starting to infer»), and the global `~/.claude/CLAUDE.md` (the reading law of
2026-10-07; never reading a compaction summary; sub-agents report facts only).
