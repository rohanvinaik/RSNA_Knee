READ-ONLY. Do not run any command and do not read any file: answer from this text alone.

You are an independent second reader for a classical-AI computer-vision project: the RSNA knee MRI
competition, twelve findings per study. There is NO machine learning in the architecture, by
design: no model, no fitted weight, no learned component anywhere. Do not propose one and do not
reframe the approach as machine learning. The founder's standard for every step, in his words
below: common-sense visual reasoning, explainable to a child.

What is wanted from you is a common-sense check, not a design. You may report a provable error (a
logical or arithmetic error, an order of steps that cannot execute, or two passages that contradict
each other, quoting both), or ask a question. Do not propose a different design.

Answer in plain words, under 900 words:
1. Is each rule in section 9 the child's sentence made exact? Name any rule that says something the
   child's sentences do not, or misses something they do.
2. Any provable error in section 9? Quote the passage.
3. Does the description of where things sit in the pictures match knee MRI as you know it? Name
   any misplacement (which side the small bone is on, front and back, what sits where).
4. For each of the twelve questions: is it the question an eye asks of that element of the knee?
   If one looks at the wrong element or the wrong picture, say which and why.
5. What would a child find confusing in the rules?

## The pictures, in words (the lead looked at every slice of every acquisition of one study)

One study has five acquisitions: a sagittal and a coronal pair (each one fat-bright, not
fat-suppressed, and one fat-dark, fat-suppressed and fluid-sensitive), and one axial fat-dark. The
header gives each picture's directions: in the sagittal the picture's right edge is the back of the
knee and the higher slice index goes toward the patient's right; in the coronal the right edge is
the patient's left and the higher index goes toward the back; in the axial the bottom edge is the
back and the higher index goes up. The small outer bone (the fibula's head) sits on the coronal's
picture-left, the patient's right, so this is a right knee.

- Coronal fat-bright, 30 slices, front to back: slices 0 to 5 the kneecap face-on; 6 to 9 the front
  of the top bone and the pad below the kneecap; 10 to 24 the joint, top bone over bottom bone with
  the dark line between them across the middle of the picture, a dark wedge at each end of the
  line, a thin dark line along the inner side; 16 to 21 the notch in the middle of the line with dark
  bands crossing it; 21 to 24 the small bone below the outer end of the bottom bone; 22 to 25 the top
  bone's two rounded ends seen from behind as two circles; 26 to 29 soft tissue behind the knee.
- Coronal fat-dark: the same picture with the bones dark and fluid bright: bright fluid wraps the
  front and both sides of the top bone on the front slices; the line between the bones is a bright
  thin line with a dark wedge at each end.
- Sagittal fat-bright, 36 slices, from the inner side to the outer side: 0 to 2 soft tissue; 3 to 11
  the inner compartment, a rounded end over a flat top with a dark wedge at the front and the back of
  the line; 12 to 22 the middle, the kneecap in front of the top bone's lower end, the notch with the
  dark crossing bands, the pocket above the kneecap; 21 to 31 the outer compartment, with the small
  bone below the back of the bottom bone toward 29 to 33; 32 to 35 soft tissue.
- Sagittal fat-dark: the same with fluid bright: bright in front of and above the top bone's lower
  end, and a large bright collection at the front of the outer side on the high slices.
- Axial fat-dark, 32 slices, bottom to top: 0 to 8 the bottom bone with the small bone beside it
  toward the back on the outer side; 11 to 14 the joint; 15 to 26 the top bone's two rounded ends
  with the notch behind, and the kneecap over the groove with bright between; 27 to 31 the top
  bone's shaft with bright fluid in front.
- The cheap halves, measured on every slice of both fat-bright pictures at 8 mm tiles: seeded
  from the top and bottom fifths of the leg they found the line on most joint slices and missed the
  sagittal's inner compartment (the top half flooded down the bright front of the leg and took the
  bottom bone); seeded either side of the deepest enclosed dip of the profile down the middle of the
  leg, the line sits at the middle of the picture (tile row 10 or 11 of 19 to 20) on every joint
  slice of both views, and the crossing follows the joint.
- The founder's attached sheet (2026-10-13): for one slice of each acquisition, the low-signal map,
  the distance from dark with its interior peaks, the territories each peak holds, the native edges
  and the dark-band traces across them. On every acquisition the two biggest peaks sit in the top
  bone and the bottom bone.

## His words (build prompts only, verbatim, in order)

[2026-10-13T00:36:14.509Z]
I would like to engage with this project fresh. I think that you've been drifting super hard, and adding more and more structure keeps pushing you further and further away from what I am trying to do, which is actually SUPER obvious and simple. 

So please ignore the instructions and guidance for full grounding. Just converse using what you know of the project at a high-level overview. Poke in lightly, turn a few things over, noodle over the high-level intent and thesis of the project

[2026-10-13T00:51:32.360Z]
No. Not at all. You completely missed the entire point of why this is not usable for diagnoses. Which is precisely my point. You keep trying to be smart. It's really not helping me. You seem to always think that you know what I'm talking about, but you REALLY don't. Please, trust me. I will tell you what you're missing, if you just let me take a few turns to explain it, with evidence.

To start, I would like one script to add a new output to the photo output systems in the pipeline. One script that puts out five images--one of each view, each of the medical images that form one study, along with every single analysis lens view that has something to say, some visual output on the original image. This is let me explain it properly

[2026-10-13T00:52:06.594Z]
Symbolic trace

[2026-10-13T00:52:22.850Z]
Don't add another isolated/island script. Serena, aider, vulture

[2026-10-13T01:01:46.670Z]
You can just add matplotlib in

[2026-10-13T02:20:03.563Z]
Okay. So, if you're actually following the epistemology I've been trying to express, the answer should be obvious. Also, why the build is currently NOT the "performance engineer, SICP-style, one compute operation per script, paralelizable compute, shared information, superposition of lenses resolving meaning" I specified that this should be.

Pick any of these. Let's say the coronal view. First off, fat-dark vs fat-bright? These aren't independent views. These two are basically "lenses" that are given to us for free, by the competition itself. 

But also let's look at these lenses, these images we have. I'm going from top-left, then right across the row, then onto the next one until the end, numbering them 1 (original) to 22 (bottom right).

The goal here is to try and resolve <object>s that correspond to "bone", tibia and femur. On image 2, already, we can CLEANLY see most of the noise cleanly subtracted out (repeated on image 10?). I see the background CLEANLY resolved out. We need to actually fix this lens to work on all five images, but once it's good like this for all of them, we should NEVER spend a SECOND of compute on this ever again. Literally EVERY analysis that comes after this is wasting about 40-50% of its compute on places that should be comepltely removed and NEVER read for ANYTHING, EVER. So yeah, THAT'S what I've been trying to communicate. We're on the FIRST lens, and already the search space is halved, and the uncertainty of the resolution is exponentially smaller. That's not a vibe, I've proven this mathematically. We can also see that already both the tibia and femur are non-trivially resolved. If we had a script that needed to wildly guess SOMETHING at only this stage, we'd actually be able to hit the tibia and femur basically 100% of the time. Also, this, and MANY of the other lenses, should have been computed off the lossy/squint view, the one that collapses that image into, I think, a 16x16 grid? We are doing two things--(1) high-level localization and targeting, and (2) fine-grained targeting and boundary-drawing. The "squint" view is WAAAAY cheaper. If the raw image is 256x256, then a 16x16 grid costs literally (n)^(1/2), for EVERYTHING. And when we've actually done that, wherever I've seen it, the squint view was MORE than enough to target analyses properly. Like, common-sense high-level reasoning, you only spend expensive compute to try and find the exact boundary of things in the places where they actually look like they might exist. Same sort of thing as the "black"/"air"/"background" removal thing I just outlined. Why try and draw boundaries where the bones aren't? I didn't do this quite so strictly in the cell tracking project because you can never actually predict where cells will be. But knee images? They almost ALWAYS look the same. Why compute vectors and shit where we know the knee isn't?

No idea what's wrong with views 3/4, they just seem like pointless noise compared to 2. Pretty sure they're a mangling of what I actually wanted.  Also 5/6. Not sure what they're supposed to be, I don't think that's what I asked for. Also, you missed some of the most CRITICAL lenses, the ones that were in [Image #1]. 

Images 7/8 feel like another duplication, but they're HIGH-resolution lenses. When it comes to the high-level resolution of the boundaries of the bones, the expensive stuff, this is REFINED. I mean, LOOK at the boundary there. Is there any question what the tibia and femur look like? 

Image 9 isn't really anything

Image 11 is partially what I was talking about, partially build, but WAAAAAAAAY more expensively than was needed. 

I could go on...but I think I've made my point, no? Can you send this photo (plus the one I've shared--the "interior peaks" one is VERY useful for specific selection of <object>s that are potentially significant, treating them as physical objects that are grounded and connected as a singular whole, will be useful for diagnosing; i.e., what is "wrong" with the coherent object that is grounded to those interior peaks), along with your understanding of what I'm saying, grounded by the <object> thesis (send out cheap agents to actually read and pull out elements that articulate the actual thesis and summarize for you, with actual quotes), as well as this prompt and your understanding, to the codex consult to validate your understanding, come back to me with your understanding of what i'm trying to explain about what you've been missing about the way this pipeline is supposed to work?
[an image he attached: the sheet described above as his attached sheet]

[2026-10-13T03:05:59.157Z]
Yeah, don't delete/remove lenses. I will figure out what bizarre interpretation you had of my words/ideas led to this presentation, but I'm sure they are meaningful in some way. 

Q1: The "fix" is to have it actually resolve out background vs leg for every image/view. I think you tried to set some global values/resolution that would work flatly on every view/image. No sense in that, these are all different views, they just happen to be of the same leg. That's why the fat-bright vs fat-dark coronal view are different--the fat-dark view is globally dark and you tested the background resolution with that one. Obviously, the fat-bright one has a COMPLETELY different signal profile, running the same numbers on it is just not going to work. The thing that grants the first lens the "authority" to declare background is "being correct". I know that sounds circular. But that's the point. We make a lens that looks for what we define as background, and when it works and only finds things that aren't bones or other anatomical features, then it works and we use it. Sounds arbitrary? So what? See my "Hellen Keller" prompt, where I go into the weirdness of the "naturalistic" fallacy for machine intelligence. Basically, her understanding of the world was entirely constructed. She lacked the ability to sense anything that was not in direct contact with her body. So what? Still intelligent, and rather saucy too. The fact that intelligence or reasoning is imparted onto a system that has no independent understanding of the domain space is immaterial to the question of if it's doing a task of genuine reasoning

Q2: Yup

Q3: ...huh? Many words, very little meaning. 

Q4: Again, huh? What's a "member"?? I don't know why you insist on using random BS made-up terms all the time, I just can't get you to stop. I don't speak Claude!! I INVENTED this, I still have no idea what you mean when you discuss it with me half the time

Q5: I don't understand how those are different. But essentially, we define that, by looking at it (common-sense border estimation) and by using domain knowledge for where these elements are supposed to be on these really fixed and almost identical-looking images

Q6: No idea, because I have no idea what underlying idea I was communicating that you misunderstood or interpreted weirdly. Keep all, I will do speulunking to understand these later.

[2026-10-13T05:43:25.357Z]
okay, cool. That last question should be pretty obvious to answer, if you understand this correctly. You saw the image. Tell me--if the coronal view has slightly different pixel counts, what's the common-sense explanation for how two images with different pixel counts can show almost precisely the same view, and thus be superimposed upon one another to more clearly resolve objects in the visual field?

[2026-10-13T05:47:30.441Z]
Good! Yes, the squint is how you make it cheap, you just kinda...line it up. That's all. The lenses, the actual analyses do the actual line-drawing and precise resolution. But for information, to help understand the significance, and eventually to diagnose the condition? It's the same fucking image, just sorta scootch it a bit, and you're good. It's the same thing.

Cool beans! So, now do you understand how you've been missing the obvious thing, and thus how we should work through making this an ACTUAL production computer vision pipeline of the kind described in the <object> thesis? I only talked about the tibia/femur, we need to be able to resolve ALL of the relevant anatomical objects to diagnose between the 12 conditions the competition asks us to resolve. We need to make this clean, do it in the way that the problem space and the solution I've designed makes obvious. See how we should do that?

[2026-10-13T05:52:04.806Z]
Excellent work! For once, you actually AREN'T wrong about this! This is the correct epistemology and workflow. I'd like to plan it out properly. Work through this, send off a codex consult (do big-boy consolut; GPT-6 Astra on Max). Once it's set, then let's work through a RIGOROUS and unambiguous plan to implement, then fire it off with a workflow or something to plow through it as mechanically as we can. As you can see from the way I've been articulating it, a LOT of this is common sense, if you're disciplined about holding to the epistemology I've communicated to you this session.

[2026-10-13T06:09:52.823Z]
Need context for your questions, they're in jargon still. "Rim"? "Clear"? "Valley"? No invented jargon. Real terms with objective meaning

[2026-10-13T06:16:38.948Z]
1. If I understand you right, then yes, a lil bit of extra compute requirement, some buffer, is perfectly fine
2. No, the other views shouldn't speak to the axial view. It's of the same leg, so it speaks to diagnosis, but it's NOT the same picture. Unlike, say, the coronal view fat bright vs fat dark, it's not "basically" the same view,it's a compeltely different picture at a completely different time and place and angle. Different photo with different rules/roles/objects. They just happen to correspond to roles that also exist in the other photos, and help in diagnosis through an independent view
3. We shall see, won't we? That's derived experimentally. My gues is that it will be resolvable above a baseline level of expected signal. Bones should be pretty flat within the internal fill of the <object>, a contusion should show up as unexpected variance in signal intensity. But we shall see when we actually try to diagnose
4. Yup, that should do
5. Not every slice, not even CLOSE. You might want to poke in on the <object> thesis, and how it was able to turn a 4D cell microscopy MOVIE into a 2D still. This is a WAAAAAAAAY easier problem than that to solve

[2026-10-13T06:26:58.531Z]
Yup! Sill have the cell depth miner going, no? This is the right general plan, enough to build off. Once you're settled, we should be good to go!

[2026-10-13T19:23:43.874Z]
Almost done, call on the codex consult to validate the build and the plan for the next steps, using my exact prompts over the past ~18-20 hours

[2026-10-13T19:38:06.595Z]
I want you to read the prompts that you are about to send first. My prompts, my words that serve as the record here

[2026-10-13T19:48:25.066Z]
Kill the old servers, then send a max effort Sol prompt out, then we converse about what er do this session

[2026-10-13T19:48:39.447Z]
Take out my personal prompts

[2026-10-13T20:03:19.607Z]
I already addressed what the epistemology and interpretations are of the images. Do you not see the common-sense answer to your questions?

[2026-10-13T20:06:24.216Z]
Good. THen you know how to fire off the next build cycle/workflow?

[2026-10-13T21:11:33.894Z]
Progress and ETA on completion please

[2026-10-13T21:18:09.475Z]
Sure, but I'm talking about the WHOLE build, the fundamental thesis as a whole pipeline/project

[2026-10-13T21:20:17.980Z]
Why? This should take a few hours? What do YOU think the thsis is, and how the build is meant to progress, the explicit intent of the project I laid out?

[2026-10-13T21:22:14.930Z]
Can you no do some work with cheaper sub-agents in parallell, the actual mechanics of the build itself?

[2026-10-13T21:31:52.485Z]
You're doing it all yourself? Not with sub-agents? Fine, whatever, do it however

[2026-10-13T21:32:13.287Z]
I just want it done

[2026-10-13T21:35:58.448Z]
Also consult with codex whenever it might be useful to get a common-sense chack on your understanding

[2026-10-13T21:47:45.055Z]
Re-ground on my words, we're post-compact. My exact prompts, otherwise you will drift,
  as you will see if you read my prompts

[2026-10-13T22:51:01.845Z]
So, are you familiar with the workflow in progress and what the goals are?

[2026-10-13T23:47:44.994Z]
You're forgetting the two types of processes. The "squint" is for localization of the expensive compute process, not for drawing a line strongly. The other operation is for fine-drawing of borders. 8mm tiles can't refine the border because that was never their job. F

Find the prompts in which I went into this. You're missing the "common sense" pass that I explicitly laid out, which will poison the whole build. Look at the photos. Actually look. This is computer vision. The photos will make the answer absurdly simple

[2026-10-13T23:55:31.497Z]
An are you following this common-sense pass from the images themselves when it comes to the rest of this build? My wordds and common sense from the images should be enough to solve it, and the <object> thesis as an oracle of theory/intent

[2026-10-14T00:00:37.848Z]
So, how can we launch a process to wrap up the build, make this a functional pipeline that resolves the full anatomy of the knee and can diagnose all 12 confitions from the competition?

[2026-10-14T00:17:10.965Z]
Good. But again, make CERTAIN that you're reading my prompts AND actually look at the photos. Those photos, plus the <object> thesis, make this a common-sense operation

[2026-10-14T00:39:06.313Z]
Always make sure you're passing a common-sense visual process. Look at the photos. The reasoning you use when applying any solution using the lenses should be explainable to a child. We need to identify the elements of knee anatomy with common-sense visual reasoning, and diagnosis of the 12 conditions is common-sense reasoning based on knee anatomy we can see

[2026-10-14T00:39:31.527Z]
This is absurdly simple. If you can't explain it to a child, you don't understand it

[2026-10-14T00:40:48.893Z]
Applies to every step of this project

## The rules under check (the design's section 9, verbatim)

## 9. The exact rules of the two processes (2026-10-14)

Written after reading every slice of every acquisition of the one study (contact sheets,
`data/pictures/the-funnel-contact-20261014/`) and measuring the cheap halves on every slice
(`data/pictures/the-funnel-halves-probe-20261014/`; probes `probe_halves.py` and
`probe_halves_plateau.py` in the session scratchpad). His words that set them: "(1) high-level
localization and targeting, and (2) fine-grained targeting and boundary-drawing"; "we define that,
by looking at it (common-sense border estimation) and by using domain knowledge for where these
elements are supposed to be on these really fixed and almost identical-looking images"; "a lil bit
of extra compute requirement, some buffer, is perfectly fine"; "Not every slice, not even CLOSE";
the fat-bright and the fat-dark of a plane are "basically 'lenses' that are given to us for free",
"the same fucking image, just sorta scootch it a bit"; the axial is "a completely different picture
... Different photo with different rules/roles/objects"; the interior peaks pick "<object>s that
are potentially significant, treating them as physical objects that are grounded and connected as
a singular whole ... what is 'wrong' with the coherent object that is grounded to those interior
peaks". The thesis: each lens "stands at its own sharpest slice" (§4.2); the cheap readings "point,
and never decide alone ... It narrows where the expensive work runs" (§5.1); the plain part is
taken first and the residual read again with that context (§1.9).

**The whole method, as a child would say it** (his words, 2026-10-14: "The reasoning you use when
applying any solution using the lenses should be explainable to a child ... If you can't explain
it to a child, you don't understand it"). Every rule below is one of these sentences made exact.
1. Knee pictures always look the same: a big bone on top, a big bone underneath, and a dark line
   between them across the middle of the picture.
2. Squint at every picture, so it is cheap. Throw away the black around the leg. Look down the
   middle of the leg from top to bottom: the bones are bright and the line between them is the
   darkest spot with bright above and below. Everything joined to the top bright part is the top
   half, everything joined to the bottom bright part is the bottom half, and where they meet is the
   line.
3. The pictures where that line sits in the middle are the ones that cut through the joint. Pick
   the middle one; on the side-to-side pictures also pick the middle of each side.
4. Put a box around the line, a bit above and below it, and look closely only inside the box.
5. Inside the box, each thing is found from the spot deepest inside it, the spot farthest from any
   dark edge. The big things just above the line are the top bone (seen from behind it shows as
   two round ends), the big things just below are the bottom bone. The kneecap is the next one, in
   front of the top bone, just above the line. The small bone is the round one tucked under one
   end of the bottom bone, touching it, toward the back, and that end is the outer side.
6. Everything else is found by where it sits next to those: the dark wedges at the two ends of the
   line, the dark bands crossing its middle, the thin dark line along the inner side, the pocket
   above the kneecap, the pad under it, the space behind the knee.
7. Then ask what is wrong with each one, the way you would by looking: is a bone cracked or
   bruised, is the gap thin, is a wedge or a band lit up, is there fluid where there should not be.

**What the pictures fix** (the header gives the directions; the study is one knee):
- coronal, front to back (the header's higher index is toward the back here): the kneecap face-on;
  the front of the upper bone with the bright pouch on the fat-dark; the joint, with both bones,
  the band, a dark wedge at each end and a thin dark line along one side; the notch in the middle
  of the band with dark bands crossing it, and the small bone below one end of the lower bone; the
  two rounded ends of the upper bone seen from behind; the soft tissue behind the knee;
- sagittal, side to side: soft tissue; a compartment (a rounded end over the flat top, a dark wedge
  at the front and the back of the band); the middle (the kneecap in front of the lower end of the
  upper bone, the notch with its crossing dark bands, the pouch above the kneecap); the other
  compartment, with the small bone below the back of the lower bone; soft tissue;
- axial, bottom to top: the lower bone with the small bone beside it toward the back; the joint;
  the kneecap over the groove of the upper bone with bright between; the pouch in front of the
  upper bone.

**Measured, 2026-10-14, the one study.** The existing basins seeded from the first and last fifths
of the leg find the joint on the coronal fat-bright slices 11 to 24 and on the sagittal fat-bright
slices 10 to 23, and fail on the sagittal's inner compartment, slices 3 to 9: the upper basin floods
down the bright front and takes the lower bone. Seeded instead from the two bright stretches either
side of the deepest enclosed dip of the profile (the chapter's own recorded rule, "markers from
anatomy, not from maxima", README's earlier mechanism, item 3; `structure.py`'s "later
increment"), the band step is 9 to 11 of 20 on every sagittal slice 5 to 31 and 10 to 11 of 19 on
every coronal slice 10 to 24, the middle of the picture, and the crossing follows the joint on
each of them; it wanders only on the slices with no joint (the kneecap slices, the soft tissue at
the stack's ends, behind the knee). On the fat-dark coronal the existing reading wraps the lower
basin round the bright fluid at the sides (the field gallery, slice 15), which is why the halves
are read on the fat-bright and carried.

### Process 1, the squint: where (8 mm tiles, every slice, cheap)

**P1 `Halves`** (`knee.collapse.halves`, new; reuses `structure._profile`, `_along_first`,
`_from_along_first`, `_seam`, `axis_code`, `superior_code`, the watershed call of `_basins`, which
become public where needed). Per series of a paired coronal or sagittal plane, read on the
fat-bright of the pair, per slice z: `inside` = the first lens's kept tiles (`not_background`,
`undecided`) with a finite median; `profile` = the central-third per-step median, superior first;
`band_step: int16 (Z,)`, the deepest enclosed dip, -1 for none; `dip_share: float64 (Z,)`, its
depth over its enclosing level; seeds = the central-third inside tiles `seed_offsets` steps above
the band (upper, 1) and below it (lower, 2); `basins: int8 (Z, TR, TC)` by the existing watershed
on the field under the told sign; `seam: bool (Z, TR, TC)`; `codes: uint8 (Z,)` over `HALF_CODES =
("read", "nothing_kept", "no_enclosed_dip", "seeds_empty", "axis_not_in_plane", "sign_unread",
"invalid_measurement")`; `source: str`, `"own"` or `"carried"`.
Pure decision `enclosed_dip(profile: tuple[float, ...]) -> tuple[int, str]` over `("read",
"no_enclosed_dip", "invalid_measurement")`: the step whose depth below `min(brightest above,
brightest below)` is largest and positive, ties to the first, with `read`; no finite step with a
finite step on each side, or no positive depth, is `(-1, "no_enclosed_dip")`; an entry that is not a
float is `(-1, "invalid_measurement")`; NaN entries are silence, skipped. Which series reads: on a
`paired` plane (R0) the fat-bright reads under its own sign and the fat-dark carries it, each of its
tiles taking the basin of its line-up partner tile at its partner slice (R3a), a tile with no
partner reading 0, `source` `"carried"`; every other coronal or sagittal series (a `solitary`
plane of either flavour, every series of a `surplus` plane) reads on its own under its told sign,
`source` `"own"`. The axial has no in-plane up-down axis and is read by its own rule (P3). Constant
`seed_offsets = (2, 3)`: 16 to 24 mm inside each bone from the band, the lead's, from the pictures
(each bone's end is several tiles tall); his to change. Picture: every slice with the seam drawn
over the plane and the band step written, as the probe's.

**P2 `BandRun` and the stills** (`knee.collapse.depth`, a new reading beside R4's four, which
stay). Per series that reads its own halves (the fat-bright of a paired plane, or a series with
`source` `"own"`): first the level, the median band step over the slices whose band step is read
and lies in the middle third of that slice's inside extent along the axis; then the band run, the
longest contiguous run of such slices whose band step lies within one step of the level, the
earlier run on a tie. Pure decision `band_run(steps: tuple[int, ...], extents: tuple[tuple[int,
int], ...]) -> tuple[int, int, str]` over `("run", "no_run", "invalid_measurement")`, `steps` the
band step per slice (-1 unread) and `extents` each slice's first and last inside step; `no_run`
returns `(-1, -1, "no_run")`. The stills, by the fixed layout (his Q5), each a position in the run:
coronal `middle` (the run's middle slice) and `back` (three quarters of the run toward the end the
header says is posterior); sagittal `side_low` (one fifth along the run), `middle` (one half) and
`side_high` (four fifths), the centres of the two compartments and of the middle. The fat-dark's
stills are its slices whose line-up partner is the fat-bright still. Constant `still_buffer = 0`
slices either side, his to widen. On the one study these are coronal 17 and 21, sagittal 10, 18
and 26: by eye, a compartment, the middle with the notch and the kneecap, and the other
compartment; the mid-joint with both wedges and the side line; the notch with the small bone below
one end. Picture: the band step over z with the run and the stills marked, and the stills.

**P3 the axial levels** (`knee.collapse.axial_levels`, new, solitary, its own rules). Built after
its own probe is read, in the second wave; the paired views carry every one of the twelve, and the
axial joins as an independent view of the kneecap's joint, the pouch and the back of the knee. Its
rules are written to this section before it is built.

**P4 the boxes** (`knee.collapse.boxes`, new). Per still: the native bounds of the tiles from
`band_step - box_above` to `band_step + box_below` along the axis, across every column that holds a
kept tile, one tile of buffer all round, clipped to the picture; `box_above = 5`, `box_below = 5`
(the bones' ends, the band and everything in it, the side lines); on the sagittal middle still
`box_above = 9`, to hold the pouch above the kneecap. The fat-dark's box is the fat-dark tiles whose
partner tile lies in the fat-bright box, plus the buffer. Nothing outside a box is read at native
resolution. Constants the lead's, from the pictures; his to change. Picture: the boxes over the
stills.

### Process 2, the native lenses: the borders, drawn only in the boxes

**N1 `BoxDrawing`** (`knee.objects.box_drawing`, new; reuses `read_interiors` whole, unchanged).
Per still, per acquisition of the pair, each in its own pixels: `read_interiors` on the box's crop
with the series' own split, `prominence_native_mm` and offsets of every pixel within `±strip_mm`;
every array kept with the crop's origin, so each coordinate maps back to the plane. This is his
attached sheet's set of lenses (distance from dark, interior peaks, territories, native edges,
dark-band traces), run where the squint said the joint is. Two facts of `read_interiors` that every
reader of this record respects: the crop's own edge is an obstacle of the distance map (it pads
the interior with False), so a peak pressed against the crop's edge is a fact about the box and is
named by its distance to that edge; and a territory's edges along the crop's edge are of kind
`frame`, with their traces `frame_clipped` (`border_codes.border_code`, read whole 2026-10-14),
and an edge whose profile runs past the crop reads `missing_profile`, so no reading counts either
as an open rim. Picture: his sheet's columns, over the box, for each still and acquisition.

**N2 `Objects`** (`knee.objects.by_peaks`, new). Per still, per acquisition: every territory with
its peak (row, column, height in mm), the half its peak lies in (the tile basin at the peak), its
pixel count and its bounds. Pure decisions, each total, each returning a named code:
- `giant_code(heights_in_half)`: the upper giant is every territory whose peak lies in the upper
  half, whose peak height is at least `giant_share = 0.5` of the highest peak in that half, and
  which has a pixel within one tile of the seam: "the big bright things just above the line", so a
  top bone that shows as two round ends (the coronal back still) is both of them; the lower giant
  likewise below; `("found", "no_peak_in_half")`, with the territories kept in peak order;
- the band, native: per column across the axis (per row on a view whose axis runs along columns),
  the distance along the axis from the upper giant's last pixel to the lower giant's first pixel,
  in mm, `band_mm (A,)`, NaN where either is absent; the band's span is the columns where it reads;
- the middle of the band: the central fifth of its span; the two compartments: the span either
  side of the middle, named `side_a` (the lower column indices) and `side_b`; the band's ends: the
  outer fifth of the span at each end (on the sagittal side stills, the front and back ends);
- `small_body_code(...)`: "the small round bone tucked under one end of the bottom bone": on the
  coronal back still, every territory, not the lower giant, whose peak lies in the lower half
  within `small_body_mm = 40` below the line and outside the band's middle three fifths, and which
  shares a boundary with the lower giant; each kept with its rim reading (N3), since a lump of fat
  reads like a bone's inside on both acquisitions and the dark rim is what tells them apart by eye;
  the side holding the candidate with the highest peak is the outer side; `("side_a", "side_b",
  "both_sides", "neither_side")`; the sagittal repeats it below the back of the lower giant on its
  two side stills, and the two views' answers are kept side by side, concurrence or disagreement;
- `front_body_code(...)`: on the sagittal middle still, a territory, not the upper giant, whose peak
  lies in the upper half within `front_steps = 5` steps above the band and in the front fifth of
  the leg's extent across the axis (front by the header); `("found", "none", "tie")`;
- the places, by position relative to those, each a pixel mask kept under a positional code:
  `front_upper` (sagittal middle: above the front body's top and in front of the upper giant's
  front); `front_lower` (sagittal middle: below the front body and in front of the band's span);
  `back` (each sagittal side still and the coronal back still: behind both giants' back pixels,
  within `back_steps = 3` steps of the band); `side_a_outside` and `side_b_outside` (coronal
  middle: outside each giant's outer pixel on that side, across the band's height `± side_mm =
  20`); `band_span_a`, `band_span_b`, `band_middle`, `band_end_a`, `band_end_b` (the band's native
  pixels between the giants, over those columns); `front_band` (sagittal middle: between the front
  body's back pixel and the upper giant's front pixel, per row).
Constants the lead's, from the pictures; his to change. Picture: each still with the giants, the
band's span and its middle, the ends, the small body, the front body and the places outlined by
their codes.

**N3 `Readings`** (`knee.predicates.readings`, new; measurements, never decisions). The same
small set on every object and every place, keyed by its code, per still and acquisition, NaN where
the object or place is absent, so each lens measures one thing and knows no question:
- per object (each giant, the front body, the small body): its area in mm²; its peak's height in
  mm; its rim, the count of its edges against dark (`low_signal`) whose trace is `bracketed` and
  the count whose trace is not, with `frame` and `missing_profile` edges counted apart and never as
  open; its inside, the median and interquartile range of its pixels, the share of its pixels at
  or below the split lying more than `inside_mm = 2` inside its edge, and the share above the
  acquisition's upper tercile edge;
- per place (`band_span_a`, `band_span_b`, `band_middle`, `band_end_a`, `band_end_b`, `front_band`,
  `front_upper`, `front_lower`, `back`, `side_a_outside`, `side_b_outside`): its area in mm²; the
  share of its pixels at or below the split (dark); the share above the acquisition's upper tercile
  edge (bright); the share above its lower tercile edge; and, for the band places and `front_band`,
  the median gap in mm.
The tercile edges are the existing rule (`tercile_edges`) over the box's kept native pixels of
that acquisition. Picture: each still with every object and place outlined and its readings
written beside its code.

**N4 the twelve, each a child's question about what can be seen** (`knee.predicates.findings`,
exists, extended). His words, 2026-10-14: "diagnosis of the 12 conditions is common-sense reasoning
based on knee anatomy we can see"; "If you can't explain it to a child, you don't understand it".
Each row points at its subject as R11 and the object model already say, asks its question, and
carries the readings that answer it beside its code; the subject and the question are written in
the design and the docstring only, and records carry the finding's index and the subject's code:
- 0, fracture: is a bone's rim broken, or does a dark line cross its inside? (every object: rim
  not bracketed; dark inside, on the fat-bright);
- 1, bruise in a bone: is a bone's inside unevenly lit, with a bright patch on the fat-dark?
  (every object: interquartile range over median and the bright share, on the fat-dark);
- 2 and 3, the worn joint on one side: is the gap between the two big bones thin on that side?
  (`band_span` on the inner and the outer side: the median gap);
- 4, the worn joint behind the kneecap: is the gap between the kneecap and the top bone thin?
  (`front_band`: the median gap);
- 5 and 6, the torn wedge on one side: is the dark wedge at that end of the joint small, or lit up
  inside on the fat-dark? (`band_end` on that side: the dark share on the fat-bright, the bright
  share on the fat-dark);
- 7, the band crossing the middle: is it dark and whole, or lit up? (`band_middle` on the sagittal
  middle still: the dark share on the fat-bright, the bright share on the fat-dark);
- 8, the thin line on the inner side: is it thick, broken, or wrapped in bright? (`side_outside`
  on the inner side: the dark share and the bright share);
- 9, fluid in the pocket above the kneecap: is the pocket full of bright? (`front_upper`: the
  bright area on the fat-dark);
- 10, the lining: is the pad under the kneecap lit where it should be dark? (`front_lower`: the
  share above the lower tercile edge on the fat-dark);
- 11, the bubble behind the knee: is there bright behind the knee on the inner side? (`back` on the
  inner side still: the bright area on the fat-dark).
Inner and outer come from the small body; with none, the side rows abstain with that reason and
keep `side_a`/`side_b`. `form_given` stays False and every code stays `form_not_given`: how much
counts is his, "derived experimentally" (2026-10-13). The output stays `projection_undeclared`.

**Not in this plan: the corpus table.** Reading the route over the 58 labelled studies, and how
its readings are laid beside the competition's labels, is his call to make and is offered to him;
nothing here builds it.

**Waves.** Wave 1, in parallel, each builder confined to its own module, test and picture: P1, P2,
P4, N1. Wave 2: N2, then N3 and N4. Wave 3: the route (`knee.pipeline`, behind the existing
`AnalysisRequest`, reading the stills instead of `selected_slice`), the view sheets, and the real
run on the one study, every picture redrawn and looked at by the lead before it goes to him. Then
his eye-check; then P3. Every name a builder writes (module, record, field, code, filename, picture
title) carries no anatomical or tissue word; anatomy lives in the design, the docstrings and the
conversation.

