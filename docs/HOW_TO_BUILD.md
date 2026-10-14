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
- Never take the next step from a compaction summary or from your own notes. His last words in the
  record say what he asked.
- The archives are invisible. «They're invisible unlesss I tell you to look in them».

### 3. The thesis is simple: keep it simple
- «This is basically the whole thing. That's it.» Recognition is pure simple math on the lenses,
  with no AI in it. Each object is resolved at least once without being tuned to one view. Rules
  are built, not tuned. Thresholds come from domain expertise and common sense. Where it cannot
  tell, it abstains, and it is never wrong.
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
- Plain words, never jargon. «What on earth does that mean?»
- Never drawn wrong: where a picture does not hold a part, it is not named. A part the pictures do
  hold is never withdrawn to stop it being drawn wrong; it is fixed («You REMOVED shit??»).
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

Side notes he relayed the same day, each a lapse a self-check would have caught: the pipeline read
only the middle slice; the menisci were unsided; the read-first rule lived only in Claude's memory;
the recovered squint code still named a missing chapter file; the fibula rule needed the header;
the "sealed" and "shelled" signs were the removed pile's under new names; Claude's own unapproved
lines sat in `AGENTS.md`.

Earlier sessions' corrections live where they were recorded: the theory's Part V (the builds thrown
away twice; «You're starting to infer»), and the global `~/.claude/CLAUDE.md` (the reading law of
2026-10-07; never reading a compaction summary; sub-agents report facts only).
