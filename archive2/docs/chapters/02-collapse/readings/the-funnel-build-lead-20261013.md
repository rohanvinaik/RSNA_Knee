# The funnel, phase A, as built: the lead's reading (2026-10-13, written before the Codex consult)

Written before opening Codex's answer, per the consultation protocol. Facts below come from the workflow
journal (the builders' and verifiers' reports), from the run folder
`data/measurements/the-funnel-phase-a-20261013` (the one labeled study, tile 8 mm, half tile 4 mm) and
from the pictures under `data/pictures/the-funnel-phase-a-20261013/<uid>/`, which the lead looked at.
The founder's words are quoted from his prompts of this session, extracted verbatim from the transcript.
The build is the OpenSpec change `the-funnel`, units 0, 1, 3a, 2 of its tasks; the repair pass of the
workflow was still running when this was written.

## 1. What his words asked for, in order

- 00:51Z: "One script that puts out five images--one of each view ... along with every single analysis
  lens view that has something to say, some visual output on the original image." Built earlier (commit
  3e7099f, the view sheets); every new reading of this phase adds a panel to them.
- 02:20Z: "fat-dark vs fat-bright? These aren't independent views. These two are basically "lenses" that
  are given to us for free"; "We need to actually fix this lens to work on all five images, but once it's
  good like this for all of them, we should NEVER spend a SECOND of compute on this ever again"; "this,
  and MANY of the other lenses, should have been computed off the lossy/squint view ... a 16x16 grid";
  "you only spend expensive compute to try and find the exact boundary of things in the places where
  they actually look like they might exist".
- 03:05Z, Q1: "The "fix" is to have it actually resolve out background vs leg for every image/view ...
  these are all different views ... running the same numbers on it is just not going to work. The thing
  that grants the first lens the "authority" to declare background is "being correct" ... when it works
  and only finds things that aren't bones or other anatomical features, then it works and we use it."
  Q6: "Keep all".
- 05:47Z: "the squint is how you make it cheap, you just kinda...line it up ... It's the same fucking
  image, just sorta scootch it a bit"; "we need to be able to resolve ALL of the relevant anatomical
  objects to diagnose between the 12 conditions".
- 05:52Z and 06:26Z: the plan approved ("the correct epistemology and workflow"; "the right general
  plan, enough to build off").
- 06:16Z: 1 "a lil bit of extra compute requirement, some buffer, is perfectly fine"; 2 "the other views
  shouldn't speak to the axial view ... it's NOT the same picture"; 3 contusion "derived experimentally";
  4 "Yup, that should do" (terciles over the leg tiles, then each object's own places); 5 "Not every
  slice, not even CLOSE".
- 18:30Z, on how to build: "do the really simple thing I'm asking for".

## 2. What is built, against each

**0, the pairs.** From the series table's own flags: Sagittal paired, Coronal paired, Axial solitary.
Matches 02:20Z (the two acquisitions of one view are the free lenses) and 06:16Z #2 (the axial stands
alone). Drawn as a caption line on the study sheet. Verified; two findings for repair: the drawn words
for a plane whose flags are all unreadable say "no series of this plane", which is false; the saved
identifier lists are not validated as lists.

**1, the squint over the stack.** Every slice of every series cut into 8 mm tiles, one grid per series:
20 x 20 (the 320 px planes at 0.5 mm, 16 px tiles), 19 x 19 (the 384 px coronal at 0.39 mm, 21 px
tiles), 20 x 20 (the 400 px sagittal at 0.4 mm, 20 px tiles); medians, extrema, coverage, and every
tile's centre in the scanner's millimetres. Matches "a 16x16 grid ... (n)^(1/2)". Verified; one real
defect for repair: the guard that keeps one grid per series compares only the grid's shape, so a
spacing that changes partway while the tile count stays would be stacked as one grid.

**3a, the line-up.** Per paired plane, on the fat-dark series: the nearest fat-bright slice along the
normal (every slice within the slab; the two normals 4e-5 degrees apart; the selected slices 15 and 15,
18 and 18, 0.0001 mm apart) and per tile the fat-bright tile whose centre is nearest in millimetres.
Sagittal pair: 400 of 400 tiles matched, centres 0.07 mm apart. Coronal pair: 360 matched, 40
"beyond_half_tile": the whole top row and left column, because the fat-bright picture covers 150 mm
against the fat-dark's 160 mm, so its first tile centre lies about 5 mm inside the recipient's and the
recipient's outer ring has no partner centre within the 4 mm bar; the nearest partner tile still
overlaps every one of those 40 tiles' footprints. Matches "the same image, scootch it a bit": the
scootch on the coronal is a couple of millimetres, the same direction over the whole knee. The
verifier's refutation: eight of the 40 edge tiles hold leg, so task 3a.1's check as declared ("every
leg-region tile matches within half a tile") does not hold on this pair. The lead's reading: that is the
edge of the smaller field of view, not a failure of the lining-up; whether an edge tile whose partner
tile overlaps it but whose centre is farther than half a tile counts as the same patch is his bar to
rule, not a defect to fix in code.

**2, the first lens.** On all five views, every slice, every tile: background, leg, or undecided, under
the series' own valley (its whole-volume histogram's first valley past the air's spike), background
being a tile every pixel of which lies at or below the valley AND which reaches the picture's border
through such tiles. Counts over the stack, background / leg / undecided:

| view | valley | background | leg | undecided |
|---|---|---|---|---|
| sagittal fat-bright | 7.34 | 237 | 11480 | 2683 |
| coronal fat-bright | 9.19 | 591 | 8191 | 2048 |
| coronal fat-dark | 22.52 | 3320 | 6647 | 2033 |
| sagittal fat-dark | 5.39 | 278 | 11465 | 2657 |
| axial fat-dark | 21.81 | 4872 | 6269 | 1659 |

Against Q1, "only finds things that aren't bones or other anatomical features": on every sheet the lead
looked at, no background tile sits on bone, muscle, fluid or skin; where the lens speaks, it is right.
But it speaks very unevenly. On the axial and the coronal fat-dark (valleys around 22) the air around
the leg is cleared broadly on every slice and the undecided ring runs one tile wide along the skin: the
picture the design described. On the two sagittals and the coronal fat-bright (valleys 5 to 9) it
clears almost nothing on the central slices (zero background tiles on sagittal slices 0 to 15) and a
few corner tiles on the later ones; the undecided ring sits at the picture's border, not at the skin.
The reason is in the numbers: with a valley that low, the darkest 16-pixel tile of air still holds a
pixel above it, so "every pixel at or below the valley" rarely holds. This is the case Q1 named ("these
are all different views ... running the same numbers on it is just not going to work") and the plan
reserved for him: "A view that fails gets its own rule, declared here as a new task with its provenance
before it is written." The lead attaches no verdict; it is E1, his look.

Consequence the lead reads from it: on those three views the lens is correct but nearly silent, so the
halving of later compute he described is not yet realized there. Nothing downstream is wrong; it is not
yet cheap.

## 3. Where the build moved past his words, by the lead's own check

- The route still runs every whole-field form (the structural reading, the volume digit maps, the
  interiors and traces, the same-orientation conversation) on every series at every run. The first lens
  is produced and saved, and nothing yet reads it or skips work because of it. "NEVER spend a SECOND of
  compute on this ever again" is declared (task 13.2, the `whole_field` switch) and not yet in force.
- The gate's law test that every produced reading has a reader is red: the line-up and the first lens
  are produced and their readers (the tile digits, the conjunction) are later units. Nothing was changed
  there. How the gate should read a producer whose reader is declared but not yet built is his to rule.
- The peak-height floor of 8 mm (the side agent's note he relayed) is in the design and nothing is
  built on it yet.
- Two small things the builders added and named rather than hid: the match code "beyond_half_tile" for
  the field-of-view edge; the seven silences a line-up picture can be in. Both are readings kept, not
  decisions made.

## 4. The next steps as declared, and the lead's uncertainties

In tasks.md order: 3b the tile digits (terciles over the leg tiles, per series); 3c the two together
per pair; 4 the chosen slices (four cheap readings per slice, each read at its peak; the cell build's
literal rule traced first); E2; 5 the dome at the squint; 5b selection by structural facts; E3; 6 the
strip and the outline; E4; 7 facing pairs; 8 the spaces between; 9 spans and envelope; E5; 10
ownership; 11 bundles, predicates, output; 12 pictures; 13 the route; 14 the 58.

The lead's uncertainties, stated as such and not as proposals:
- 3b on a view where the first lens cleared little: "leg tiles" would then include most of the air, and
  the terciles would be read over air as well as knee. Whether 3b waits for the view's own rule, or runs
  on the views as they are, follows from E1.
- The rule for choosing slices in 4 is the lead's (each cheap reading at its peak), not his; so is the
  axial's rule in 5b, the mapping of each condition to its object in 11, and every constant in design
  §3.
- The coronal pair's edge ring (the 40 tiles) is a bar question before 3c reads the two together there.

## 5. Questions for him, in plain words

1. On the two sagittals and the coronal fat-bright the lens clears almost nothing; is that a view that
   gets its own rule now, or do we go on with those views as they are?
2. On the coronal pair the fat-bright picture is 10 mm narrower than the fat-dark; the outer ring of
   tiles has a partner tile overlapping it but no partner centre within 4 mm. Same patch, or not?
3. The gate test that every reading has a reader stays red while the line-up and the first lens wait for
   the digits. Accept the red until then, or something else?
4. Terciles over the leg tiles on a view where the lens cleared little: run it, or wait?
5. Is "each cheap reading at its own peak slice" what you mean by "not every slice", before it is built?

## Addendum, the same day, before the consult was sent

- The workflow ended in an error after unit 2 was built: its verifier returned no report, so unit 2 is
  unverified by a second reader and no repair pass ran. Section 2's "verified" stands for units 0, 1
  and 3a; for unit 2 it does not apply.
- The picture he attached at 02:20Z is the objects stage's gallery (five series, six readings each,
  the interior peaks among them), the "[Image #1]" of his words. The 22-panel sheet he numbers is the
  coronal fat-dark view sheet of 2026-10-12 (`view-frames-20261012/…/study-views/03-coronal-fs1-fat1.png`),
  which was not attached. The packet's first bracket had the two the wrong way round and is corrected.
- Three lines of his were missing from the packet and are added: 17:19Z, mid-turn, "All the prompts
  from the whole session, not just this past compact. You've compacted SEVERAL times"; the unchanged
  re-send of 17:26Z at 17:27Z; and the fragment "Yeah, I can'" at 18:00Z.
- The verifiers' findings that the packet had left out are now in it: the builder-authored decision in
  unit 1's picture adapter, the two refusals the builder of unit 3a added, the four-against-five code
  drift in unit 0's declaration and design rule, and the forty coronal edge tiles being the top row,
  the left column and one corner-adjacent tile.
- Two sends. The first, GPT-6 Astra at xhigh, carried every prompt he typed this session, his messages
  of 05:19Z to 05:34Z and 17:18Z to 18:33Z included. He then said "Take out my personal prompts", and
  the second send, GPT-6.1 Sol at xhigh ("a max effort Sol prompt"), carried the packet without them.
  The file `workbench/consults/the-funnel-build-prompt-20261013.md` holds the second form.
