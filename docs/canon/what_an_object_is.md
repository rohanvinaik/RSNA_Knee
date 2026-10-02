# What an \<Object> Is

*Classical-AI computer vision from the laws of what we see, shown on four-dimensional fluorescence
microscopy of cells*

Rohan Vinaik and Claude (Anthropic)

October 1, 2026

## Abstract

We argue that a computer can understand a picture by reasoning from what the objects in it are and
how the instrument makes them visible. This is computer vision as Minsky and Papert conceived it:
building and reasoning with descriptions of objects, their relations and what they can do. The
\<object> of our title is the kind of thing a general computer vision must recapitulate: contiguous
and closed, persistent, moved by physics, and signaling by known laws. We state the thesis as four
hypotheses, each resting on the one before. A structure built from the domain's laws resolves most
of a picture cheaply, through deliberately lossy views, borders drawn from the data's topology, and
the removal of each \<object> found together with the signal it spreads. What a removal leaves is the
same problem with added context. Every measurement at every scale is written in one exact language
of balanced-ternary digits (−1, 0 or +1) in orthogonal banks, compared by one exact cosine. The
bundles that language needs to compare \<objects> are exactly the substrate of Minsky's K-lines,
memories that re-create what was active in a past success, and of his censors, memories that prevent
an interpretation. Once an expert confirms a case, its bundle is the cue of a K-line, and recall
brings back the interpretation the case confirmed and the procedure it routes to. An expert teaches
this memory once, in a few hours and a few dozen examples, and it moves the borders the structure
draws. A society of independent agencies, each taught by its own clean signal, takes up only the
questions the structure leaves open. Truth among them is assigned by concurrence, and where no
answer can be proved the system abstains. Learning is meant in the classical sense: a departure from
the expected, kept with its context. We show each element working, one at a time, on
four-dimensional fluorescence movies of cells on a plate, where the task is to find and follow every
nucleus. We state what generalizes to X-rays, histology, MRI, faces and logic puzzles, and what
would show the thesis wrong.

## 1. Vision: What an \<Object> Is

Our goal is a computer that understands what a picture shows. To build one, we believe we must
answer two questions: what it means for a computer to see, and what a computer must know before it
can see anything. Our answer to the first is Minsky and Papert's. Our answer to the second is the
title of this paper: it must know what an \<object> is.

### 1.1 Seeing Is Describing

Computer vision, in the sense Minsky and Papert gave it, is a computer building and reasoning with
descriptions of objects: their parts, their relations and what they can do (Minsky and Papert,
1971). It is not a mapping fitted from pixels to labels. A description can be checked against what
its objects must be, and corrected where it is wrong.

Descriptions are possible because visual data is not raw data. Raw data lives in pure mathematics:
an array of numbers obeys nothing but arithmetic, and any array is as possible as any other. Visual
data is constrained by what the human visual system is built around, because what it shows has
physical presence. Things in a picture are contiguous and closed, the gestalt by which we see a
shape as one thing. They persist through time. They move and fall by Newton's laws, and no two of
them occupy one space. The signal that shows them obeys the physics of the instrument: light obeys
optics, and X-rays are absorbed by what they cross. Most of the arrays a camera could record are
pictures of nothing that could exist, and a computer that knows the laws can rule them out before it
looks.

### 1.2 The \<Object>

The angle brackets of our title are the computer scientist's type notation, and they carry the
thesis. An **\<object>** is not a thing in the world. It is the kind of object a general computer
vision must recapitulate: what the human visual system recognizes as a thing, with physical presence
(contiguous, closed, persistent, moved by physics, signaling by known laws). Humans reason on
objects; computer vision reasons on \<objects>.

Each domain has its own \<object>: a nucleus under a microscope, a nodule in a chest X-ray, a face in
a photograph, a shape in a puzzle's grid. Each is a persistent thing whose appearance follows known
laws. A system built on the thesis holds its domain's concept of the \<object>, and from it reasons
about what each candidate in a picture is and is not. An expert teaches it once, cheaply: a few
hours, a few dozen examples of what the target looks like and of what is noise or wrong. Then it
understands the picture, reasons on it and proposes interpretations, by the explanatory steps a
person uses: objects, constraints, examples, interpretation. The correspondence explains the design;
it is no claim about the mechanism of a brain.

### 1.3 The Thesis, and Where It Holds

> **The thesis:** Where what we look at is made of persistent physical objects whose appearance
> follows known laws, a computer can understand the picture by reasoning from what those objects are
> and how the instrument makes them visible. It propagates those laws through deliberately lossy
> views, writes everything it measures in one exact language, and remembers an expert's confirmed
> examples as K-lines and censors that act back on what it does. Only the residue is learned, in the
> classical sense: each departure from what was expected is kept with its context, so the mistake is
> pre-empted when the context recurs; nothing is a fitted weight.

The thesis holds where **the precondition** of the companion paper, *Structured Symbolic AI*
(Vinaik, 2026), holds:
- The domain's laws can be stated;
- Its state is discrete, with one true answer at each moment;
- Each of its instrument's lossy views, cheap readings that drop detail on purpose (§3), can be read
  against one law;
- Each learner has a signal that is clean for what it learns: one that does not depend on what it is
  learning (§10.1);
- The laws can be checked on the output.

§2 shows that the running instance (§1.6) meets each clause; §13 sets out the recipe for any domain
that does.

We say once, plainly, what the system is not. Nothing in it is a model fitted to data: no weight is
adjusted until outputs match examples, no feature is learned, and no loss is minimized. Its
knowledge is in its laws, its lossy views and an expert's confirmed examples. Its learning is
learning in the sense of Minsky and Winston (Minsky, 1986; Winston, 1970): a departure from what was
expected, kept with how it was off, in what context and about which role of which typed object
(§7.1). Nor does it guess. An answer is given only under proof, by the contract of the step that
gives it, and where none can be proved the step abstains and the abstention is kept (§4.8). The rest
of the paper shows all this by what the system does.

### 1.4 Four Hypotheses

We state the thesis as four hypotheses. Each rests on the one before. They are dependencies, not
deductions: each needs a further claim to carry it, and we state that claim as its bridge.

**H1. Vision built from the laws.** A structure built from the domain's laws resolves most of what a
picture shows, cheaply, by three moves.
- *The collapse* (§3). The laws say along which dimensions an \<object> barely changes, and along
  those the data is read coarsely on purpose. A few cheap views, each answering one question about
  the whole, stand in for the full record, and a few moments are resolved in full while the rest are
  followed from them. Reducing a signal on purpose answers a categorical question more cleanly and
  more cheaply at once, as squinting resolves a gestalt: the squint.
- *Borders in the data's topology* (§5). An \<object> is a region the structure can enclose:
  contiguous, of a sane shape, around a center its signal rises to. Its outline is pulled taut, and
  two \<objects> never occupy one space.
- *Elimination under law* (§4). What is knowably not an \<object> is removed, and each \<object> found
  is taken out of the data whole, together with the signal it spreads around it. What is left is not
  noise but the same structured problem with added context, read again until nothing \<object>-shaped
  remains: the Wayfinder thesis.

*Bridge:* the laws license exactly these losses and these removals. What the structure leaves is a
typed **residue**, not noise: the questions it leaves open, each typed by how it arose (§10), never
the residual data its rounds read (§4.6).

**H2. One exact language.** Every measurement at every scale is written in one language, so that any
two readings can be compared and any difference named (§6).
- Each measured quantity is a balanced-ternary digit, −1, 0 or +1: below, at or above a fixed
  reference, its static middle. A reading that is a word, such as the route by which an \<object> was
  found, is written as that word.
- The digits are written in banks, blocks of the vector whose rows are exactly orthogonal, so that
  no two values blur. A silent bank, the informational zero, says that nothing was read there.
- An \<object>'s profile is the bundle of its places (positions of the picture's grid, §3), kept as
  whole-number counts.
- Comparison is one exact cosine over only the banks a question reads, and a difference decodes to
  named banks. No single number means anything; meaning is a profile in context.

*Bridge:* the profiles keep the distinctions each question needs. That is measured for each domain,
never assumed: an exact code does not make an observation lossless.

**H3. The bundles are K-lines: taught once, fed back into seeing.** The bundles the language needs
to compare \<objects> are exactly the substrate of Minsky's K-lines, memories that re-create what was
active in a past success, and of his censors, memories that prevent an interpretation (§7).
- An expert's call on a candidate becomes a case. The case's bundle is the cue of a K-line: recall
  brings back the interpretation the case confirmed and the procedure it routes to. The call's
  digits against an interpretation are remembered censors.
- The expert teaches the memory once, for one kind of image (§8).
- The memory then moves the line the structure draws between noise and \<object> (§9).

*Bridge:* similar situations generally lead to similar results, Winston's precondition for reasoning
by precedent (Winston, 1980). The memory moves the borders geometrically; the expert's calls
establish that they are right.

**H4. A society learns only the residue.** What the structure leaves is taken up by a society of
agencies, each with its own question, its own clean teaching signal and its own cases (§10).
- Each agency asks one of the questions a domain puts to its \<objects>: is this candidate one
  \<object>, was any \<object> missed, where is each, and what becomes of it. They meet in the one
  language and the kept record of findings. Truth among them is assigned by concurrence and refused
  on disagreement, and each decides or abstains.
- Where the record runs through time, identity comes first and position is then cheap (§11). A few
  moments, the **anchors**, are resolved in full, spread through the record and none at its border,
  with spans of two lengths that tell a steady drift from a random wander (§3.4).
- Between the anchors each \<object> is carried by what its laws let it do. The small wander those
  laws allow bounds where to look, and a cheap look is taken at every step.

*Bridge:* law checks (nothing overlaps; nothing \<object>-shaped is left) support a judgment; an
independent signal establishes it.

### 1.5 Why the Design Looks as It Does

One idea lies under every element of the design. A problem's structure carries information from
outside any local question into it. The design hands its computation to that structure: the physics
of the domain and its instrument, what its \<objects> can and cannot do, and a world in which every
\<object> is accounted for by law. The local question is then answered cheaply, and a local error is
corrected by what surrounds it. Each element of the design is an instance:
- The signal an \<object> spreads goes out with it, because once the \<object> is known, the physics
  explains that signal (§4.5);
- A lawful removal changes the meaning of what remains, as the host's opening of a door does in the
  Monty Hall problem (§4.6);
- Every place's vector holds every scale it belongs to, as a strand of DNA is repaired with
  information the strand alone does not hold (§6.1);
- Where \<objects> barely change, the system gets each one's state once and measures the change, the
  smaller number (memento mori, §2.2);
- Each anchor has time on both sides, so its truth must survive a small step either way (§3.4);
- An \<object> that goes missing or appears is an inconsistency to resolve, and its answer is stated
  only when it is shown (the sandwich, §11.5);
- What something is not tells what another thing is (reading by exclusion, §3.6; the censors, §7.5).

The design has a spirit as well as a why: economy. A domain's laws are also its economy. Physical
things change only as their laws let them, and living things spend energy only where they must; most
of a scene, most of the time, does nothing new. The system keeps the same economy: it does the least
computation that answers. It gets each \<object>'s state once and then measures only the change;
where a law already answers, it computes nothing. It resolves a moment in full only at its anchors,
or where a bound on the error of what it carried says it must.

### 1.6 The Running Instance

We show the thesis on four-dimensional fluorescence microscopy of cells on a plate: cells grown on a
plate for microscopy, each nucleus carrying a fluorescent label, recorded as a movie of volumes
through time. The task is to find every nucleus at every time point and to follow each through the
movie. The hosts who released the movies marked a random sparse sample of the nuclei by hand; we use
that annotation only while building and teaching, never in a run. The expert who taught this
instance is one of us (Vinaik).

Each element of the system is shown working on real data, one at a time. The claims are about what
each element computes and why: integrating the elements is engineering, and this is not an
engineering document. The examples are chosen for clarity, and the deliberately hard cells of the
teaching appear where the paper treats noise correction and robustness (§9).

What we do not claim follows from the bridges: that an exact code makes an observation lossless,
that a law check establishes a judgment, or that this instance's lenses, laws and teaching carry to
another domain. The recipe carries, and §13.3 names the measurements that would show the thesis
wrong.

### 1.7 Lineage

We continue the Minsky and Papert conception of vision as building and reasoning with descriptions
of objects, their relations and their possible actions (Minsky and Papert, 1971). The tradition that
conception belongs to includes Roberts's machine perception of three-dimensional solids (Roberts,
1963), the summer vision project (Papert, 1966) and Guzman's decomposition of scenes into bodies
(Guzman, 1968). It includes Winston's learning of structural concepts from scenes of blocks
(Winston, 1970), and Waltz's line labeling (Waltz, 1972), which builds on the labeling schemes of
Huffman and Clowes (Huffman, 1971; Clowes, 1971). They are a tradition, not a chain. Vision was a
formative arena of classical AI, and this paper returns classical AI to it with a new substrate. The
learning machinery is Minsky's and Winston's (Minsky, 1979; Winston, 1970); the substrate and the
composition are new. Parts of the design began in earlier work by one of us (Vinaik), on
abstract-reasoning puzzles and on encoding DNA (§13.4).

### 1.8 Road Map

Figure 1 draws the whole system. The paper's arc is a loop: the structure sees, the language
writes, the memory remembers and is taught, the memory then helps the structure see better, and a
society organizes what remains, including time. §2 sets down the world under the microscope and its
laws, and shows that the domain meets the precondition. §3 to §5 establish H1, §6 establishes H2,
§7 to §9 establish H3, and §10 and §11 establish H4. §12 gives the mechanics beneath the language
and the memory, §13 what generalizes and what would show the thesis wrong, and §14 concludes.

```
 A MOVIE: 64 slices × 256 × 256 voxels (about 104 µm a side), at each of about 100 time points
                         |
                         v
 THE COLLAPSE (the squint)
   In depth:  Four lenses (Gradient, Contrast, Split Quality, Dark Share), each standing
              at its own sharpest depth, read the volume as flat stills; the composite,
              a fifth flat picture, keeps each place's depth as a number
   In time:   Three anchor time points (t/3, t/2, 2t/3), dividing the movie into a third,
              a sixth, a sixth and a third, are resolved in full; every other time point is
              followed
                         |
                         |  At each anchor time point
                         v
 +------------------------------------------------+
 | THE LOOP, round by round (Figure 11)           |
 | Stage 0  Each lens's flat picture of its own   |
 |          depth, the composite, and the cheap   |
 |          readings                              |
 | Stage 1  The black                             |
 | Stage 2  The bodies                            |
 | Stage 3  The lenses speak; every cell counted  |
 |          once                                  |
 | Stage 4  Commit, and pull-out of each cell     |
 |          through its band, with its halo       |
 | Then the residual is read again (the site      |
 | search; reaching down), and the next round     |
 | runs on the residual, until a round takes      |
 | nothing; then the last look                    |
 +------------------------------------------------+
                         |
                         v
 THE EMPTIED BOX: Only black and scattered speckle, no cell-shaped signal
 THE CANDIDATES: Every <object> pulled out, each with its footprint, its band and how it came out
                         |
                         v
 THE VECTORS (§6): Every place written in one language, digits in banks; full vectors
 at the anchors; an <object>'s profile is the bundle of its places
                         |
                         v
 +------------------------------------------------+                  +----------------------------+
 | THE CLEAN-UP, on the residual                  |<=================| THE MEMORY AND ITS BUCKETS |
 | On each candidate, the line between noise and  | Remembered noise | (§7, §8)                   |
 | cell: Each place goes with the remembered case | draws the line in| Cases: Each a bundle, its  |
 | it resembles most, and each piece it marks is  | A remembered cell| call, what was expected of |
 | judged against confirmed regions               | pushes it back   | it, and its source         |
 | [Agency: One real cell each]                   |                  | The clean-up's buckets:    |
 +------------------------------------------------+                  |  Noise; cell;              |
                         |                                           |  not-cell-not-noise        |
                         v                                           | The identity buckets:      |
 +------------------------------------------------+                  |  One cell; several; noise  |
 | THE CELL ASSIGNMENT                            |<---- Recall -----|                            |
 | Recall routes each <object>:                   |                  +----------------------------+
 |   One cell    -> Admitted                      |                                ^
 |   Several, N  -> The Scissors, under a         |                                | Calls
 |                  contract of N cells           |                                | become cases
 |   Noise       -> Out of focus                  |                  +----------------------------+
 | [Agency: One real cell each]                   |                  | THE EXPERT, once, for one  |
 +------------------------------------------------+                  | kind of image: Calls the   |
                         |                                           | hardest candidates the     |
                         v                                           | structure proposes, by     |
 +------------------------------------------------+                  | eye, in plain words;       |
 | EVERY CELL                                     |                  | cosine takes the easy half |
 | Finds the cells the rounds did not take, where |                  +----------------------------+
 | the analyses half-saw something; each cell it  |
 | accepts is checked as one real cell            |
 | (In teaching, the count says: Keep trying;     |
 | never a cut)                                   |
 | [Agency: Every cell]                           |
 +------------------------------------------------+
                         |
                         v
 THE ANCHOR RESOLVED: Its cells, each with its full and its cheap profiles
                         |
                         |  Between and beyond the anchors
                         v
 +------------------------------------------------------------------------------------------------+
 | FOLLOWING THROUGH TIME: Identity first, then position (§11)                                    |
 |   Each cell is carried from an anchor, forward and backward, by the static model (between      |
 |   two anchors, the line through its two full positions; beyond them, the plate's drift),       |
 |   and by the jiggle, whose draws by Monte Carlo give its envelope                              |
 |   A look at every step: The cell's cheap profile against the next picture's cheap vector       |
 |   The guarantee bounds the mean error of a context's carried places at a span; as that bound   |
 |   nears the tolerance, the Ephemeris move resolves the time point in full again, starting      |
 |   from the prediction                                                                          |
 |   Between t/3 and 2t/3 each cell is carried from both sides; a cell missing or appearing is    |
 |   an inconsistency to resolve, its answer stated only when it is shown (the sandwich)          |
 |   [Agency: Position]                                                                           |
 | DIVISION: The dean reads the story of each cell's light along its track; where it divides, the |
 |   mother's track ends and two daughters begin, linked; no two cells merge (the no-merge law)   |
 |   [Agency: Division]                                                                           |
 +------------------------------------------------------------------------------------------------+
                         |
                         v
 THE OUTPUT: Every cell at every time point, each linked to itself at the next time point,
             and each mother linked to her two daughters

 [Agency: ...] marks where each of the four agencies acts (§10); they meet in the one language
 and the kept record of findings.
```

*Figure 1.* The whole system, from a movie to its output. The movie is collapsed twice: in depth,
into the four lenses' flat stills beside the composite; in time, into three anchor time points
resolved in full, from which every other time point is followed. At each anchor the loop runs round
by round on the residual until a round takes nothing, and the last look leaves the emptied box.
Every place is written in one language, and each candidate becomes the bundle of its places. The
clean-up and the cell assignment both read the memory the expert taught once; the double arrow is
the feedback into seeing. Between and beyond the anchors, each cell is carried and looked at every
step, the guarantee bounds the mean error of carried places, and the dean reads division along its
track. The bracketed tags mark where each of the four agencies acts.
 Its terms are defined where the paper takes them up: the guarantee and the Ephemeris move in §11.4,
the dean in §11.6.

## 2. The World Under the Microscope, and Its Laws

How a computer should read a picture depends not on how messy it looks but on whether we know the laws that
generate it. A fluorescence microscope's pictures look noisy, yet they record not an unstructured world but many
structured processes, superimposed and seen through a lossy instrument. By a **law** we mean a physical or
biological regularity the system reasons from. Here there are four: the optics of the light; biology's economy of
energy, with time's arrow inside it; the plate's drift; and one cell to one place.

### 2.1 The Movies, and How a Nucleus Shows Itself

A nucleus shows itself by its own light, which obeys known laws; so a model of the light is a model of where the
nuclei are.

A **movie** is one four-dimensional recording of **cells on a plate**: cells grown on a plate for microscopy, which
crowd and touch where they are dense. A movie has about 100 **time points**, and at each the microscope records one
volume: 64 slices 1.625 µm apart in depth, each a grid of 256 × 256 voxels 0.406 µm on a side. The volume is 104 µm
a side. Each cell carries a fluorescent label in its **nucleus**, so here "cell" and "nucleus" name the same
\<object>. A nucleus is 4 to 13 µm across.

A voxel's value counts the photons the camera caught there, and light from different nuclei adds. Each nucleus
spreads its light around itself, in the plane and, out of focus, over neighboring slices. This is its **halo**,
which fades with distance by the inverse-square law, a bright nucleus's reaching farther. Where cells crowd, a
diffuse light, the **haze**, fills the gaps between them. With no light the camera still gives a reading, the
dark, which varies with time point and depth. Its **flicker**, its variation around the true light, grows as the
square root of the light.

Figure 2 shows the three plates this paper reads, from above: a crowded plate, cells beside open
field and a sparse plate. On the crowded plate, nuclei touch, and haze fills every gap. Where two
nuclei touch, brightness alone does not say where one ends. The laws narrow it: each is one closed
region of its own light, its halo falls away by the inverse-square law, and the two cannot hold one
place.

![Three Plates, Seen From Above](figures/F01.png)

*Figure 2.* The three plates this paper reads, each at the middle of its movie (t/2), seen from
above: at every place, the brightest value down the volume's 64 slices. Each panel is the whole
field, about 104 µm a side, on its own brightness scale. (A) A crowded plate: nuclei packed across
the whole field, brightest at the lower right. (B) Cells beside open field: a band of packed nuclei
from the top left to the bottom, open dark field to its right. (C) A sparse plate: fewer nuclei,
spaced apart along a curved band at the right, a few larger, blurred lights beside it, the left half
dark. White crosses edged in black mark the annotated nuclei, the hosts' random sparse sample of the
cells.

### 2.2 A Rigidly Structured World: Memento Mori

Biology looks random and is the most structured domain there is. Life wins order from entropy, and energy is its
deciding oracle: every process costs energy, so one that does not serve life needs a strong reason to have been
kept. So cells act in extremely logical ways, and the space of what they might do collapses: under the microscope
they sit, jiggle, and divide when the time is right. We call this concept **memento mori**: the name recalls that
life is mortal, and lasts only by spending its energy where survival and propagation need it. The movies narrow it
further: one cell type, on a plate, with one signal.

A cell moves, generally, for one of three reasons. Its surroundings move, and it goes along rather than spend energy holding on,
so cells mostly move together and slowly: their shared motion is the plate's drift. It divides, or its neighbors
push it: two objects cannot hold one space, yielding costs less than resisting, and a pushed cell moves by
Newton's second law. Or chance moves it a little, since holding still would itself cost energy: this small random
walk is **the jiggle**. Cells do not wander or push back against the mass: their own steps are small against the spacing between neighbors (§2.4). In depth they barely move, being fixed
to the plate; free-floating cells are washed off when it is prepared. A division is a one-time cost that doubles
the chance of persisting and clears the maintenance debt built up in one cell; one cell becomes exactly two.

The system mirrors the biology: if the cells are not moving, it does not pretend they are. It gets each cell's
position and measures the change, the smaller number.

### 2.3 Time's Arrow, One Cell to One Place, and One True State

Inside memento mori runs time's arrow: cells are born, live, divide and die, never in reverse. Its consequences
include laws that forbid outright: two cells never merge, and no division is undone. Nothing appears from nowhere
or vanishes without a cause; a daughter existed before, as its parent. So a cell missing at a time point, or one
appearing, is an inconsistency whose cause the system must look for (the sandwich, §11.5).

One cell to one place: two \<objects> never occupy one space. Two at one place and depth are one \<object> to settle;
at different depths, different cells.

The state a movie records is discrete. At every moment there is a true, countable set of nuclei at true places,
and from one moment to the next a true answer to which nucleus is which. So every **law check**, a test of a law
on the output alone, passes or fails, and a failure names a mistake.

### 2.4 What Comes With the Movies, and What Is Measured

Two things come with the movies from the hosts, and neither is used in a run.

**The annotation** follows a few cells through each movie, each marked by hand as a point at its
nucleus's center on one slice and linked from one time point to the next, divisions included. The
hosts describe it as a random sparse sample of the cells, not a census: on the crowded plate of
Figure 2, a single white cross marks the nucleus it follows there. **The hosts' check** matches
a reported position to an annotated nucleus within 7 µm. The nuclei it checks are drawn at random,
so the task is every cell. In building and teaching, the annotation has four uses: 1. A check: every
annotated cell lies inside a taken cell (§4.8); 2. In teaching, a reading: N annotated nuclei in one
candidate mean at least N cells; 3. The yardstick a carried position's error is measured against; 4.
In teaching, its divisions confirm divisions for the division agency.

**The count** is the hosts' estimate of the cells in a movie, one number totaled over its time points; shared
evenly, it says roughly how many cells a time point holds. It is used only in teaching. It establishes how many,
never which: it is the every-cell agency's oracle for how many cells remain to find, and it supports, never
establishes, any judgment about one object; nothing is trimmed to meet it.

Measured on the annotation of the movies we worked with, four facts make the laws usable:

| Law | Measured on the annotation | What it licenses |
|---|---|---|
| Cells barely move | A nucleus moves 1.82 µm from one time point to the next at the median, 4.14 µm at the 90th percentile, 8.38 µm at the 99th | Following cells by small shifts (§3, §11) |
| Depth barely changes | No change in depth at the median; 3.25 µm (two slices) at the 90th percentile | The collapse into flat stills (§3) |
| Division is rare | 0.12 divisions for every hundred links between time points | Following ordinary cells as the rule, with every track read for division |
| Nothing merges | No marked nucleus has two predecessors | A merge in the output is always an error |

Most steps are small against the spacing: measured at a few time points, a nucleus's nearest neighbor lies 7.1 to
7.8 µm away at the median, center to center. Following only a few cells, the annotation cannot say whether
division is rare on the plate or only among those cells. So no step depends on that rate: every cell's track is
read for division (§11.6).

### 2.5 Why the Laws Matter: Seeing as a Constraint Problem

The laws turn seeing into a constraint problem, the idea under the design: the problem's structure carries
information from outside a local question into it. Coloring the map of the contiguous United States with four
colors by depth-first search, in an order arranged to be bad, would by Winston's estimate outlast the universe.
Reducing at each step the colors still open to the neighbors of the state just colored, and propagating the
reductions, catches a blunder where it is made and takes seconds (Winston, 2010). Waltz's filter found a unique
label for each line in his first scenes from the junctions at its ends, its work growing linearly with the number
of line segments rather than exponentially (Waltz, 1972).

Here the laws are that structure. A place a known nucleus holds, no other can hold. The drift and the jiggle bound
where a nucleus can be next, so its identity is carried, not searched for. The no-merge law strikes every merge
before it is considered. The optics make a known nucleus's light computable, so it can be taken out with its halo
(§4.5), leaving the same problem with added context.

### 2.6 The Precondition, Met

This domain meets each clause of the precondition.

- *Its laws can be stated:* the four set down above, and the camera's dark and flicker.
- *Its state is discrete, with one true answer at each moment.*
- *Each of its instrument's lossy views can be read against one law:* the laws hold depth, and short spans of
  time, nearly constant, so each can be flattened without losing the answer (§3).
- *Each learner has a signal clean for what it learns.* Each agency is taught from its own: the count, an expert's
  calls, full resolutions, and the divisions the annotation marks (§10.1).
- *The laws can be checked on the output.* A law check fails where the output holds two nuclei in one place, a
  merge, or a nucleus that is not one contiguous region of a sane shape (§5.1). It fails where a cell appears or
  vanishes unexplained, where one cell carried from the anchors on either side lands in two places (§11.5), or
  where cell-shaped light still stands when the work is done. Each check supports a judgment; only an independent
  signal, such as an expert's call or a full measurement, establishes one.

## 3. Collapse: Reading a Four-Dimensional Movie as Two-Dimensional Stills

The first move of **H1** (vision built from the laws) is to stop rereading what a movie's laws hold nearly constant.
We call the move **the collapse**: the movie is read as flat two-dimensional stills, one for each lens at its own
depth, and time is followed by small shifts from three time points resolved in full. A **place** is a position of the
256 × 256 grid in a flat picture; at a slice, a voxel. The collapse is the first instance of **the squint**: reducing
a signal on purpose, so that a categorical question resolves more cleanly and more cheaply.

### 3.1 The Warrant

The collapse is licensed by how nuclei move. As measured on the annotation, a nucleus's depth barely changes from one
time point to the next, and most of its steps are small against the spacing to its neighbors. When cells move, they
mostly move together and slowly, with the drift of the plate or of a region.

Invariance in depth does not put the cells in one plane. Within one time point, the annotated nuclei spread over a
median of 18 of the 64 slices in some of the movies we worked with, and over 46 in others. What is nearly invariant is
each cell's own depth, since it is fixed to the plate. So the collapse makes several flat pictures, each at its own
depth, never one.

### 3.2 Four Lenses, Each at Its Own Depth

Each nucleus is sharpest at its own depth, so a flat picture at a well-chosen depth holds the nuclei there whole: the
physics of focus. A **lens**, in general, is a cheap, deliberately lossy view that measures one thing and knows no
question. No answer is built into it: only the step that reads it takes its value as evidence for or against anything
(§4.5). Here the four lenses are independent measures of how in focus a slice is:

1. Gradient: the mean squared brightness gradient across the slice (Sobel's, down and across, never through depth);
2. Contrast: the variance of the slice's brightness over its mean;
3. Split Quality: how cleanly the slice's brightness falls into two groups, bright objects and background (the best
   between-group variance, as a share of the whole; Otsu, 1979);
4. Dark Share: the share of the slice's places at or below the camera's dark.

Gradient and Contrast are the classical autofocus measures (Groen, Young and Ligthart, 1985; Sun, Duthaler and Nelson,
2004); Split Quality and Dark Share are ours. The four are co-equal, and each often sees what the others miss. Blur
softens steps, merges the two groups and smears light into the gaps between cells, so each lens reads highest where a
slice is sharpest. Each lens stands at its own sharpest slice and draws the **bodies** it sees there, contiguous
regions that stand out in its picture. A lens with nothing clear to say abstains. Nothing is averaged or merged.

Figure 3 works this through on one crowded plate at t/2. Gradient and Contrast stand at slices 61 and 63 and draw
much the same bodies. Split Quality and Dark Share stand near each other at slices 33 and 27, farther from the first
pair than any nucleus is wide, and draw another layer of the volume. Lenses at about one depth read one plane two
ways, and each corrects the other's borders; lenses at different depths are the three-dimensional structure itself.

![The Four Lenses and the Composite, Each at Its Own Depth](figures/E2.png)

*Figure 3.* The four lenses and the composite on a crowded plate at t/2, in the first round
(§4.6), each lens at the slice it scores sharpest, named above its panel. The classical autofocus
measures are in violet: Gradient, at slice 61, and Contrast, at slice 63. Ours are in gold: Split
Quality, at slice 33, and Dark Share, at slice 27. (A) Where each picture is domed, a bright center
with a darker surround at a nucleus's scale, among the places stage 1 keeps (§4.2), with specks
narrower than 2 µm removed (§4.3). (B) The bodies each lens draws there, each outline pulled taut
(§5.1) as the lenses read each other (§4.4). The two pairs stand at two depths and draw different
layers of the volume. (C) The composite, every place shown at the sharpest slice of its nearest
bright spot: left, where it is domed; right, the borders of its spots' territories. The white cross
marks an annotated nucleus, drawn for the reader.

### 3.3 The Composite: Depth Kept as a Number

**The composite** keeps depth another way, as a number at each place: since each nucleus keeps its depth, one number
per place can hold it. Bright spots are found through the whole volume at a nucleus's scale. Each is given its own
slice: the one, near where it was found, at which the light over a nucleus-sized disc around it is brightest. Every
place of the grid is shown at the slice of its nearest spot and keeps that slice as a number (Figure 3, last
column).

The composite finds signal across depth that the four lenses miss. It is also the least clean of the five pictures, so
it never pulls a cell and never decides alone: it points. Where it shows light that no lens holds, the lenses that can
speak there are asked (the site search, §4.6).

The lenses' four pictures and the composite, each with its depth recorded, are **stage 0** of each round of a full
resolution (§4). Depth is peeled, never reconstructed. Each cell taken leaves the volume through its band, the slices
it occupies, together with its halo, and the next round reads again what is left.

### 3.4 Time Collapses as Depth Does

Cells on a plate barely move, so the system gets each cell's position and measures the change, the smaller number
(memento mori). Only three **anchor time points**, t/3, t/2 and 2t/3, are resolved in full. Between them each cell is
carried by the static model (§11.1), allowed a small random jiggle, and looked at cheaply at every step
(Figure 4).

```
DEPTH, one crowded time point at t/2 (64 slices of 256 × 256 voxels)

  Slice  0 -+
  Slice 27  |-- Dark Share        \
  Slice 33  |-- Split Quality      |  Four flat pictures, each lens at
  Slice 61  |-- Gradient           |  the slice where it reads sharpest
  Slice 63 -+-- Contrast          /
            + The composite: One flat picture, each place's slice kept as a number

TIME, across the movie (about 100 time points)

  0 ....................#.........#.........#................... End
                       t/3       t/2       2t/3
    |----- A third -----|-A sixth-|-A sixth-|---- A third -----|
  #  An anchor time point, resolved in full
  .  A time point followed: Carried by the static model, looked at every step
```

*Figure 4.* The collapse, in depth and in time. Above, the four lenses of Figure 3 at the slices they read
sharpest, and the composite. Below, the three anchors, a sixth apart, divide the movie into a third, a sixth, a sixth
and a third; every other time point is followed.

The anchors divide the movie unevenly: a third of it before the first, a sixth between each pair, and a third after
the last. That one choice does three things at once. It spreads the anchors through the movie. It keeps each off a
border, so each has time on both sides. And its pairings span two lengths, a sixth (t/3 to t/2, and t/2 to 2t/3) and a
third (t/3 to 2t/3). So a steady, time-based drift can be told from a stochastic wander: over the longer span a steady
drift doubles, while a random wander grows by only about √2.

Time on both sides tests an anchor. A truth that survives a small step either way is real. A false cell, one whose
cause does not last, is unlikely to survive the steps around it, and less likely with each further step. So a falsehood bounded in time is exponentially unlikely. Anchors at the first and last time points would assert a base truth that
nothing could warrant.

Between t/3 and 2t/3 every cell has an anchor on each side, a two-sided oracle: a cell missing at a step, or
appearing, is an inconsistency to resolve (the sandwich, §11.5). Before t/3 and after 2t/3 a cell is carried from the
nearer anchor alone, so the tails are fuzzier, never gaps.

### 3.5 The Squint

Each of these moves makes the signal less detailed on purpose, because the questions asked of it are categorical:
whether there is a shape here or only blur, whether a region is one cell or two. Such a question needs a reading only
to fall on the right side of a line. The squint is cheaper and cleaner at once: for the question at hand, more usable
information from less data. No reduction adds information to the data; it removes, faster than the answer, the
variation the answer would otherwise have to see through. So signal-to-noise rises as the work falls. The companion
paper states the same principle for any domain (Vinaik, 2026). The laws say which reductions are safe: those that
flatten only what they hold nearly constant (the precondition's third clause).

The name is the familiar act: squinting at an ambiguous shape loses detail and brings out the gestalt, the contiguous,
closed whole. Figure 5 makes it literal. Reduced to each 16 × 16 square's median light, a crowded plate still shows
where its cells mass and where its ground is dark. That grid's squares are the neighborhood every place's vector
carries, read there in each lens's picture (§6.1).

![Stage 1 Clears the Black, and the Grid Shows the Squint](figures/E1.png)

*Figure 5.* Stage 1 clears the black, and the grid's medians are the squint made visible. Two
plates at the middle of their movies (t/2): above, a crowded plate; below, cells beside open field.
Left: the time point from above, at each place the brightest light down its slices. Middle: each
place at its brightest slice, colored by which of stage 1's two readings calls it black. The senior
reading asks whether the light stands above the camera's dark, here read for the whole time point
from its own counts; the junior speaks only where the senior keeps a place, and asks whether the
light stands above the haze of its slice. Dark red: black by both. Red: black by the camera's dark
alone. Light red: black by the haze alone. Gray, the light itself: kept by both. Right: the plate as
a 16 × 16 grid of tiles, each drawn at its median light over all 64 slices, the blur at which the
vectors write a place's neighborhood; tiles whose median lies below the camera's dark are bordered
in red, though a place in them may stand above the dark at its brightest slice. Crosses mark
annotated nuclei, drawn for the reader. Beside open field, most of the plate is cleared before any
cell is looked for.

Reducing the signal seems to run against Waltz's result, that precise distinctions produced his unique labels (Waltz,
1972). It does not: each lens is coarse, but the lenses' joint description is precise, independent readings each bound
to what it measures, with every disagreement kept and none pooled into one score.

### 3.6 What One Step Removes, and What Is Kept

The savings compound, and nothing needed is lost. In a round each lens draws the whole field from one slice of the 64,
and full resolution runs at three time points of about 100. Stage 1 (§4.2) clears what any eye would call background
before anything is drawn (Figure 5, middle), and each later step works only on what earlier steps left.

Every loss is taken in a view or in how a reading is written, never in what is kept or in the exact arithmetic on it.
Stage 1 deletes nothing: what it clears from one lens's picture stays in the volume for every other lens and every
later round. How coarse a view may be is measured (§12.4). What a view misses, a later round reads again, and between
anchors every step looks again at the raw picture. When a bound on the mean error of a context's carried places says
they can no longer be trusted, the time point is resolved in full (§11.4).

The views can afford to be cheap because of **reading by exclusion**: a reading that is poor at finding a signal can
be reliable at saying where the signal is not. What something is not tells what another thing is, so what the lenses
set aside is defined away, not lost. In one pass on cells beside open field (Figure 6), the lenses' bodies are not
clean cells, but they lie on the cells, and over the open field none draws at all.

![The Wire Diagram: The Lenses in One Pass, and What Only the Composite Holds](figures/E4.png)

*Figure 6.* The wire diagram, on cells beside open field at t/2, in one pass. (A) The four
lenses' bodies, each lens at its own depth (its slice named in the panel's note), outlined in violet
for the classical pair and gold for ours, over the brightest light down the slices. The drawings are
not clean cells, but they lie on the cells. (B) The composite, every place at the sharpest slice of
its nearest bright spot, with its wire in cyan, the borders between the spots' territories where
stage 1 keeps the place. (C) What only the composite holds. The places any lens drew are darkened,
and the composite's sites are filled in cyan: places where the composite holds a bounded bright
thing that the lenses' pictures do not, stage 1 keeps the place, no lens drew a body, the light
stands above its local base, and the patch is wider than a speck. White crosses mark annotated
nuclei, drawn for the reader.

The collapse turns a four-dimensional search into flat, categorical questions, each asked where the laws say its
answer lies.

## 4. The Structure: Stages 0 to 4, and the Loop That Empties the Box

A time point is resolved when the system can say of every place in its volume whether a cell is there, what its
shape is, and that it is one cell and not noise. Here we establish how the structure settles most of this from the
laws alone: elimination under law, the third move of **H1** (vision built from the laws). Each stage removes only
what a law says is not a cell, or takes out whole what the laws say is one. What is left is read again, until **the
box**, the whole three-dimensional volume of the time point, holds nothing cell-shaped.

One pass of stages 0 to 4 over what is left, closed by two targeted searches, is a **round**. The loop runs at
each anchor time point, and §11 follows the cells through every other time point. Whether each object taken is one
cell, and not noise, is settled on the candidates (§7 to §9).

### 4.1 Stage 0 and the Natural Philosopher's Toolkit

Stage 0 sets out what every later stage reads: the four lenses' flat pictures, each at the depth its lens chose,
and the composite. Beside them stand cheap readings, which we call **the natural philosopher's toolkit**. Each is
made once, in milliseconds, where its input first exists, and kept for any stage to consult. These readings point,
and never decide alone. A coarse view of the whole field is itself a squint: it settles whether a plate is dense or
sparse, still or moving, more cleanly and cheaply than a fine one. It narrows where the expensive work runs, and its
reading of the drift routes how the cells are followed.

The readings of the whole field, taken once for the movie, are the **priors**: its density, its distribution (even,
spiky or one-sided), its profile down the depth, and whether and how the plate drifts. Their words form the
**regime key** a case from this field is kept under. Each round takes the same readings over each lens's picture
and over a 16 × 16 grid of squares laid on it. It keeps them, so the vectors can write each place's surroundings as
they stood when its cell came out.

### 4.2 Stage 1: The Black, by Seniority

**Stage 1, the black**, removes from each lens's picture what is knowably not signal. It reasons from the camera's
dark and the haze (§2.1), by which black is local, never one number. In the movies we worked with, the darkest
thousandth of a movie's voxels reads anywhere from 2 to about 500 camera counts.

Two filters act in order of seniority, a rule of authority. The senior filter removes every place with no light
above the camera's dark, calibrated for each frame and depth. It is narrow and knowably correct: it does not fire
wherever light is faint, but where it fires it is right, and it decides alone. Where it keeps a place, the junior
filter removes what does not stand above its local haze, read over the nearby hollows between bodies within a fixed
radius of the place. The junior, the stronger reading inside busy regions where the senior cannot cut, refines only
after deferring.

Stage 1 deletes nothing: its removals shape the bodies one lens draws on one slice, and the voxels stay for every
other lens and every later round. That is what **there is no noise** means: a removal is a decision by a reading
entitled to make it, kept as a record, never a discard. The principle does not deny what an expert calls noise,
light that belongs to no cell. It says that nothing is discarded unexplained, and that a disagreement between
correct readings is information.

### 4.3 Stage 2: The Bodies

**Stage 2, the bodies**, reasons from the gestalt of an \<object>: contiguous, closed, and of a size a nucleus can
have. It joins the open places that stand above their local base, the mean light of the open places around them,
into contiguous bodies. It removes the specks, bodies narrower than 2 µm, since nothing that small is a nucleus,
and it stitches back fragments of one cell. "Stage 1/2" names the black and this clearing together.

No body is parted here, even one with two bright centers. Every parting waits until the object's own light is apart
from the volume, after the take. The Scissors then part it under a contract of N, the number of cells a call or a
recall gives it (§7.2).

### 4.4 Stage 3: The Lenses Speak

In **stage 3, the lenses speak**, and truth is assigned by **concurrence**: assigned where independent readings
agree, refused where they disagree, never by one tuned pipeline or one voice. Each lens measures one thing and knows
no question, so no reading wins by being brighter. The lenses meet by depth alone. Each body's outline is first
pulled taut (§5.1), and two lenses at about one slice then read one plane two ways:
1. Where their bodies agree, each corrects the other's border;
2. Where a partner draws two bodies where a lens holds one, that parting is carried forward to after the take;
3. A lens alone at its depth keeps every body, since each lens often sees what the others miss;
4. Where two disagree, neither overrules the other.

The result is a cleaner set of each lens's own bodies, never a merged picture: cells are pulled from the lenses.

Every cell the round's lenses hold is then counted once, by the law that two \<objects> never occupy one space. A
cell's **footprint** is the places it covers in the plane, and its **column** is that footprint followed straight
down through every slice. A **hump** is one rise and fall of light down a column. Two lenses' bodies lying mostly
over one another are one cell where one hump holds both lenses' depths, and one cell over another where none does.
Figure 7 shows the counting on cells beside open field, in the first round.

![How Many Lenses Draw Each Place, the Cells Counted Once, and the Residual](figures/E3.png)

*Figure 7.* How many lenses draw each place, the cells counted once, and the composite's
residual, on cells beside open field at t/2, in the first round. (A) At each place, how many of the
four lenses' bodies hold it, each lens at its own depth, drawn over the composite from darkest green
(one lens) to lightest (all four). Much is drawn by one lens alone: the lenses stand at different
depths, and each holds cells the others do not. (B) The cells, each counted once (orange outlines);
since no body is parted before the take (§4.3), one outline can hold more than one nucleus, taken
whole and parted later. (C) The composite's residual, the composite made again from what the first
pass leaves. Cyan outlines its sites, where it still shows light that no lens holds, which the site
search asks the lenses about (Figure 9). White crosses mark annotated nuclei, drawn for the
reader.

### 4.5 Stage 4: Commit by Concurrence, and the Pull-Out

**Stage 4, commit and pull-out**, takes out each cell the views agree on, together with the light it spreads. It
reasons from the optics of a known cell (§2.1). Read alone, faint light beside a bright cell could pass for a dim
cell. Once the bright cell is known, the optics say that light is its own, so the take corrects for what a known
cell did to its surroundings.

The commit, the take's first check, reads apart each independent reading of one counted cell that can speak, never
pooling them into one score, and only the commit reads a reading as for or against. Where they concur, the cell is
taken, the concurring readings recorded; where they disagree or abstain, it stays for the next round, which reads
it from scratch. A narrow reading may count one way only: the commit reads whether the light at a place is domed
above its surround as for, never against, so that no blurred nucleus is rejected on its word.

The **pull-out** takes a committed cell out in three dimensions, never as a flat cutout with its depth left
floating. Its **band** is the slices it occupies down its column, the hump its own slice sits on. The cell goes
together with its halo, and this taking is **the halo removal**. In the plane, at each slice of the band, the take
holds the footprint and its drop-off, the cell's own light still falling away past its edge. It leaves the halo's
thin outer reaches to the haze, which is read again each round, and sets the voxels taken to black: to their
slice's haze, so that no false edge appears. In depth, above and below the band, the take subtracts from the cell's
column the light the inverse-square law says the cell spreads, out to its reach (§5.5). What remains is the slice's
haze, or another cell's own light, so a cell stacked beneath survives for reaching down to find.

The optics give the take a second check, which needs no annotation: once a cell is out, its place should look like
its surroundings. A ring means too little came out, a hole too much, and a lobe a second cell; a patch darker than
the camera reads with no light is impossible. Every object taken is a **candidate** until it is called.

### 4.6 The Loop: The Residual, the Site Search and Reaching Down

What a round leaves is the **residual**: the volume after the cells found so far have been pulled out with their
halos. By **the Wayfinder thesis**, named after earlier work by one of us (Vinaik), it is not noise. When the plain
part of a structured problem is classified and removed, what remains is the same kind of problem with added
context, so the structure reads it again. Its signal-to-noise is higher for the loss: what stood hidden beside a
bright cell stands out once that cell is gone.

Figure 8 shows this on a crowded plate at t/2, which this section follows. The first round takes its cells,
leaving dark holes, while cells at depths no lens of that round read still shine through. On its own brightness
scale the residual is a plate again, of fewer, fainter cells, the flashy signal of the obvious ones gone, and the
second round takes them.

![The Pull-Out, in Color](figures/E5b.png)

*Figure 8.* The pull-out in color, on a crowded plate at t/2, seen from above: at every place,
the brightest light down the slices. (A) The time point as recorded. (B) Every cell the first round
takes, each filled in its own color (the colors only separate neighbors): the cells the lenses drew
and counted once, those the site search found, and those found by reaching down. Each is lifted out
of the volume through its band, together with the light still falling away from it in the plane, and
the places it leaves are given their slice's haze. (C) What the first round leaves, on the same
brightness scale: dark holes where its cells were taken, while cells at depths no lens of this round
read still shine through, for the rounds after. (D) The same residual on its own brightness scale,
and the cells the second round takes from it: fewer, fainter cells, the same kind of problem. White
crosses mark annotated nuclei, drawn for the reader.

The removal also changes what the rest means: the Monty Hall move (Selvin, 1975). Three doors hide a car and two
goats. You pick one; by the rule of the game the host, who knows where the car is, opens another, one hiding a goat,
choosing at random when both do. The two closed doors look identical, but the structure of the problem gives them
different meanings. Opening the third door moves nothing behind any door; it changes what we know. The first pick
keeps its one chance in three, and switching wins twice as often: information from outside the two-door choice,
carried by the problem's structure, changes it. The residual inherits the principle, never the numbers. Its
removal is lawful, of cells known to be cells taken with their light, so objects in the residual that look alike
mean different things, given what was removed around them. The system keeps that meaning: each candidate carries
how it came out (§5.6), and the clean-up reads it in the residual (§9.2).

The next round runs stage 0 again on the residual, every lens recomputed. Each lens stands at the sharpest slice of
the residual it has not used, so a later round reads depths the first round's cells hid, and a lens with nothing
left to say abstains.

**The site search** follows the composite, which points and never pulls. Wherever the composite of the residual
still shows bounded light that no lens holds, wider than a speck, there is a **site**. The search asks there, in a
small block of the volume through every slice, and only the lenses that can say something speak, each at a local
peak of its own focus. Figure 9 shows four sites on the same plate, where three lenses speak, then two, one and
none; where none speaks, nothing is taken. Their cells are counted once and taken like any other.

![The Site Search, With Its Abstentions](figures/E6.png)

*Figure 9.* The site search, with its abstentions, on a crowded plate at t/2, in the first round.
Each row is one site, where the composite of what the first pass leaves still shows light that no
lens holds; in turn, rows A to D show a site where three lenses speak, two, one and none. First
column: the composite of what is left around the site, the site outlined in cyan; the round reads a
block of the volume 11 µm from the site's center each way, through every slice. Middle columns, one
lens each. Above: the lens's reading of each slice of the block, depth running left to right, with
the height a peak must reach to speak, dashed, and the slices where the lens speaks named over it. A
lens speaks only at a peak that reaches that height, and then draws its bodies on the block at its
clearest slice, below, outlined in its color; a lens whose readings hold no such peak abstains. Last
column: the site's cells (orange), counted once across the lenses that spoke, which the round takes,
each whole, as every take is: an outline that holds more than one nucleus is parted after the take
(§4.3). Where no lens speaks, nothing is taken.

**Reaching down** reads the column of each cell just taken, on what is left, for a second hump at another depth:
two cells stacked in depth, a dumbbell standing on its end, which no flat picture shows as two. The taken cell's
halo has already gone with it, in the plane and in depth, so a hump that remains is not its spread light. The
lenses that can speak there are run there, and each object found is taken through its own band, its column read in
turn.

### 4.7 The End: The Last Look and the Emptied Box

The loop ends when a round takes nothing; a guard on the number of rounds is a reported safety, never the stopping
rule. By eye, what the rounds leave is clean (Figure 10). Read object by object, it still holds a few nuclei among
the blur, the pieces of taken cells and the haze.

**The last look** finds them by structure, never by one brightness number, since a bright signal need not be
cell-shaped. What is left goes through stage 1/2 at each slice's own dark. Each object still standing is read once,
at its highest point, on the untouched light: by its hump down the column, its dome (§5.2), its outline pulled taut,
and its source, the taken cell it may have come from. From these it takes one word:
1. Part of a taken cell: blur above or below it, or a piece of it at its depth;
2. Narrower than a cell: the bright but tiny;
3. Not a sane shape;
4. No dome of its own: haze;
5. A nucleus of its own, taken as a candidate like every other cell.

These words are **the last look's clearing**, each kept as a finding. What remains is **the emptied box**: the
volume holding only black and scattered speckle, with no cell-shaped signal. Figure 10 follows one slice of the
crowded plate round by round, to the emptied box after the last look.

![A Time Point Round by Round: The Wayfinder Thesis](figures/E7.png)

*Figure 10.* A time point round by round, the Wayfinder thesis: one slice of a crowded plate at
t/2. Each picture is the same slice as a round leaves it. The first round reads the time point as
recorded, and each later round reads what the one before it left, once its cells were pulled out and
their places given their slice's haze. Each picture is cleared as the last look clears what is left,
by stage 1/2 at the slice's own dark, so what is plainly black, the specks and the places taken are
black. (A) Each picture on its own brightness scale: what is left is the same kind of picture, with
fewer and fainter cells standing out each time. (B) Every picture on the first round's scale: the
slice empties. The pictures show the first four rounds and, last, the emptied box after the last
look: on the first round's scale, black with scattered specks; on its own, faint scattered light and
specks, nothing shaped like a cell.

Figure 11 draws the round and how the loop ends.

```
 (A) ONE TIME POINT SEEN FROM THE SIDE, x across and depth down; each lens stands at its own depth

           x ->
          +----------------------------------------------------------------------+
  Top     |                                                                      |
          |                       ##  <- No lens stands at its depth:            |
          |                       ##     The composite points to a site          |
          |                       ##                                             |
          |         ##                                          ##               |
          |- - - - -## - - - - - - - - - - - - - - - - - - - - -## - - - - - - - |  Dark Share
          |         ##                            ##            ##               |
  Depth   |- - - - - - - - - - - - - - - - - - - -## - - - - - - - - - - - - - - |  Split Quality
    |     |                                       ##                             |
    v     |                                                     ##               |
          |                     Reaching down: A second hump -> ##               |
          |                ##                                   ##               |
          |                ##                                                    |
          |================##====================================================|  Gradient
 Bottom   |================##====================================================|  Contrast
          +----------------------------------------------------------------------+
           ##  A cell, through its band        - - -  and  ===  The plane where a lens stands


 (B) ONE ROUND, on what is left, every lens recomputed

 +-> STAGE 0  The flat pictures, each lens at the sharpest depth it has not used; the composite;
 |            the cheap readings
 |   STAGE 1  The black: The senior filter (the camera's dark), then the junior (the local haze)
 |   STAGE 2  The bodies: Specks removed, fragments of one cell stitched
 |   STAGE 3  The lenses speak: A cleaner view for each lens; every cell counted once
 |   STAGE 4  Commit and pull-out: Each agreed cell taken through its band, with its halo
 |   THE RESIDUAL, READ AGAIN: The site search, where the composite points; reaching down
 |                |
 +------ Yes -- Did this round take anything?
                  | No
                  v
     THE LAST LOOK: Each object still standing, read once at its highest point, takes one word
                  |
                  v
     THE EMPTIED BOX: Only black and scattered speckle, no cell-shaped signal


 (C) A PULL-OUT, seen from the side (x across, depth down)

                  .     .     .     .     .     .     .     .
           .                                                       .
  {    .                       ################                        .
  {  .                  ##############################                   .
  { .                 ##################################                  .
  {  .                  ##############################                   .
  {    .                       ################                        .
           .                                                       .
                  .     .     .     .     .     .     .     .

   ###   The cell, taken out of the volume as a 3-D object through its band
    {    Its band: The slices it occupies
   . .   Its halo: The light it spreads, falling off by the inverse-square law, taken out with it,
         in the plane its drop-off, the hole set to the slice's haze, and in depth its light out
         to its reach; what stays is the residual


 (D) REACHING DOWN: The light down one taken cell's column, from the top slice to the bottom

   Light
     ^         .''''.
     |       .'      '.       <- The taken cell's hump, taken out with its halo
     |      .          .
     |     .            .                   ____
     |    .              .                 /    \        <- A second hump at another depth:
     |   .                .               /      \          Another cell in the same column;
     |  .                  .             /        \         the lenses that can speak there
     |_.                    .___________/          \___     are run there
     +------------------------------------------------------------> Depth (slices)
     The dotted hump is gone: It went out with the pull-out, so the second hump stands out
```

*Figure 11.* The loop at an anchor time point, in summary. (A) A time point from the side: each lens draws the
bodies its plane cuts. The lenses stand in the order of depth Figure 3 shows for a crowded plate, Gradient and
Contrast deepest and two slices apart, so those two read each other's bodies in stage 3; the spacing is drawn
loosely. A cell no lens's plane cuts still shows in the composite, which points to it as a site, and a second cell
in a taken cell's column is found by reaching down. (B) One round, stage by stage, each next round starting from
stage 0 on what is left, and the last look that ends the loop. (C) A pull-out: the cell leaves as a
three-dimensional object through its band, with its halo (Figure 15 draws the halo removal). (D) Reaching down:
with the first hump taken out, a second hump at another depth in the same column stands out. Each pass removes what
is plain, so the residual the next pass reads has a better signal-to-noise: the Wayfinder thesis.

### 4.8 What Supports, What Establishes, and What Is Handed On

The loop's checks support its judgments, and only an independent signal establishes them. The emptied box is a law
check (§2.6). By the laws, a resolved time point holds no cell-shaped signal, no two cells in one place and no
taken cell's light left behind, and the loop checks each on its own output. The laws cannot say that each object
taken is one real cell, or that no cell was missed. An expert's calls on the candidates establish what each one
is, and teach the memory.

The annotation and the count (§2.4) serve only while building and teaching. The annotation shows, on the cells it
samples, that none was missed: every annotated cell must lie inside a taken cell. The count is a reason to keep
trying, never a cut. A time point whose taken cells fall well short of it still holds cells for the every-cell
agency to find (§10.1). Nothing taken is removed to meet it, and no threshold moves until it fits.

Every step obeys **decide or abstain**: it settles its question or says it cannot, and never guesses. An answer it
gives is right, even when only negative, and each abstention is kept, its light left for the next round. An answer
is given only under proof, by its contract, and principled abstention is one of the strengths of a law-based
design. So the kept record of findings is whole. It is what one time point hands on: every taken cell with its
footprint, band and depth, and how it came out; every candidate; every decision with what was known before it; and
the residual. The language of §6 is written from that record, and the clean-up and the agencies take up what the
structure leaves.

## 5. Borders: The Data Topology of an \<Object>

Here we establish the second move of **H1** (vision built from the laws), borders in the data's topology, the geometry beneath every stage of the loop. An \<object> is a region the structure can enclose, and each border it draws is a law written as geometry. A nucleus shows itself by a gestalt: it is contiguous and closed, roughly round, brightest at its center, several slices deep, and it holds a space of its own. Each of those words comes from a law, and so does the halo a nucleus spreads. Contiguity and closure are the gestalt; roundness and a sane size are biology's; the bright center and the halo are the optics of a fluorescent source. The band is a nucleus's depth, one space is physics, and the camera's flicker sets how finely any border is known. Read as a relief of light, a nucleus is a peak, its border is where the peak falls to its surroundings, and a valley is where one \<object> ends and the next begins.

### 5.1 Bodies and Outlines: The Coastline Answered

A body's **outline** is its border pulled taut: the trace made as short as it can be while the body's area and topology are kept. It answers the coastline paradox (Mandelbrot, 1967). Traced place by place, a body's border is ragged with the camera's flicker: the finer the ruler, the longer the border, until its length measures the flicker rather than the nucleus. Laying an oval over the body is no remedy: it erases a dumbbell's waist, which is how two touching nuclei are told from one.

Three constraints meet in the pull. Of all loops enclosing one area, the circle's is the shortest, so shortening the trace at a fixed area rounds the shape as far as the data allow. The knowledge that a nucleus is roundish is applied as a pull, never imposed. No border is known more finely than the flicker, so none is moved farther than its flicker. And topology is kept: a dumbbell whose waist is deeper than the flicker keeps its waist and its two centers, and reaches the Scissors whole.

Each border point gets a **leeway**: how far the flicker could have displaced it, the flicker at the light there divided by how steeply the light falls across the border, between half a place and half a speck (1 µm). Then, pull after pull until nothing moves:

1. Each point moves halfway onto the chord between its two neighbors, which shortens the loop most for the least motion;
2. Each point moves halfway toward an oval around two centers that the loop's own area and second moments set on its long axis, farther apart the longer it is than wide (one center, for a round loop);
3. The loop is eased along its normal to hold the area it was traced with, and each point is held within its leeway of where it was traced.

Figure 12 shows the pull on one lens's bodies: each trace shortens, and each shape is kept.

![An Outline Pulled Taut](figures/F08.png)

*Figure 12.* An outline pulled taut: four bodies the Dark Share lens draws at slice 7 on a sparse
plate, in the first round. (A) Each border as traced, ragged with the flicker of single places. (B)
The same borders pulled taut, no point moved farther than its leeway: the trace shortened, the shape
kept; the dim fill is the places the pull shed. Scale bar 10 µm.

A shape is sane when its outline is one closed loop and its width, the diameter of a circle of its area, lies between 4 µm, the narrowest nucleus, and 15 µm, the widest one cell may be. A wider shape is taken whole, and parted after the take (§4.3). Each body is pulled taut on its own as the lenses begin to read each other, so neighbors never join across the lane between them. What a body drew outside its outline is kept as a finding, never discarded. The last look and the shape the clean-up keeps are pulled taut the same way.

### 5.2 The Dome and Its Territories

A nucleus is brightest at its center, by the optics of a fluorescent source, so the structure gives every place on a slice to a bright center. A center's **dome** is the territory of places it holds, and a place's **dome link** is its direction to that center. The centers are the peaks of the negative Laplacian of a Gaussian blur at a nucleus's scale (Marr and Hildreth, 1980), a response positive exactly where a place outshines its surround. Nothing is cut on strength, so a bright nucleus never silences a dim one. Each place goes to its nearest center in the plane.

The dome link says which places belong together. It is a cheap prior, drawn by distance alone, and it never decides alone: where it errs is information. Figure 13 works through one example, on a sparse plate. Its first panels mark a slice's bright centers, faint ones included, and give every place to its nearest center. The last two show bodies the structure enclosed, each holding two centers. The expert called the first two cells and the second one cell. Two centers alone do not make two cells, nor does one center make one cell, so where the dome link and a call disagree, the disagreement is evidence, kept. Whether a candidate is one nucleus, and where to part it, is read in part from whether its places point to one center or two. The vectors write the dome link into every place (§6.1).

![A Slice's Domes, and Two Bodies That Each Hold Two Centers](figures/S5.png)

*Figure 13.* A slice's domes, on a sparse plate. (A) The untouched light of one slice, every
bright center marked in cyan: a place brighter than its surroundings at a nucleus's scale. None is
cut on strength, so the dark field holds faint ones too. (B) Every place given to its nearest
center: each territory tinted over the light, black where territories meet, each center a black dot;
the box frames the body drawn in (C). (C) A body that holds two centers, its places tinted by the
territory each lies in, with an arrow at every second place toward its own center; the expert called
it two cells. (D) Another body, drawn the same way at its own slice, also holds two centers; the
expert called it one cell.

### 5.3 One \<Object>, One Space

Two \<objects> never occupy one space, and two at different depths are different \<objects> (§2.3). The law is applied twice.

Among the lenses' bodies in a round, those at one depth are joined and the cell is counted once, while bodies one over the other are recorded on each other and never merged. No join is forced through a middle body whose two partners lie one over the other: the column decides, and a lens standing where the column holds no hump abstains. A cell's footprint is the union of its bodies, pulled taut once more.

Among the candidates, the law is **one space**: the settling of objects that share voxels, each counted as its footprint through its band. Two that share voxels are one object to settle, never two cells by rule: two cells not yet parted, or one cell taken twice, as the expert's call and the memory decide. Two whose outlines overlap but whose bands share no slice lie one over the other: different \<objects>, never merged. Who keeps a region two candidates share is settled in the clean-up, by its ownership map (§9.5).

### 5.4 The Column and the Band

A nucleus is several slices deep, and down its column its light rises and falls once: one hump. Its band is the hump its own slice sits on, and a dip followed by a rise is the valley before another cell.

The column holds one number a slice. Each place under the footprint is put through stage 1's two filters: a place both keep gives its light above that slice's haze, in flickers of the camera, and a place either removes gives 0. The slice's number is their mean. From the cell's own slice, the structure climbs to the hump's top, the band's middle, then walks down each side while the light stands above one flicker. Where the light rises again by more than one flicker past a dip, the band ends at the dip. The cell's depth is the median, over its footprint, of each place's own brightest slice within the band, so light from a brighter cell at another depth lends it nothing. The hump's top and that median are the cell's two depth readings, and whether they agree is kept with it.

### 5.5 The Halo Goes With Its Cell

The take pulls a cell out of the volume with its halo, in the plane and in depth: the halo removal. Its law is the optics of a known source.

In the plane, at each slice of the band, the take follows the cell's drop-off without assuming its curve. It grows from the footprint ring by ring, taking each neighboring place whose light is at most one flicker above the lowest light on the way to it: light still falling away from the cell. It stops where the light turns up toward another source or sinks into the haze, and it never enters another cell's footprint or a voxel already taken. What it leaves, the halo's thin outer reaches, belongs to the haze. Figure 14 shows it on a crowded plate: with every other taken cell pulled out around them, three nuclei keep their own light.

![Nuclei Called One Cell, With Every Other Taken Cell Pulled Out](figures/F09.png)

*Figure 14.* Three nuclei the expert called one cell, on a crowded plate, one to a column. (A)
The cell's slice, untouched. (B) The same slice with every other taken cell pulled out through its
band, with its drop-off in the plane, its places given the haze; the cell keeps its own light.
Magenta outline: the cell's footprint; magenta laid over the light: the shape its clean-up keeps;
olive: material it takes off as noise; green and teal: other candidates holding part of it (right
column); orange: every other taken cell at that slice. Each column names the cell's slice, each row
the view.

In depth, the law is computed outright. A cell whose peak light stands I₀ above its slice's dark, and whose radius is r, has light falling with distance d from its center as I₀(r/d)². That light meets the dark's flicker σ at d = r√(I₀/σ), and this distance in whole slices, rounded up, is the cell's **reach**. A brighter cell reaches farther, and any cell does over a quieter dark. Above and below its band, the take subtracts from the cell's column the light the inverse-square law says the cell spreads, out to its reach. What remains is the slice's haze, or another cell's own light. So a cell stacked beneath survives, for reaching down to find. Figure 15 draws both directions in a side view of one cell.

```
 A side view through one cell's center: x across, depth down

                       Before the take                After the take
                    .......................        .......................
 Above the band,    .........:::::.........        .........~~~~~.........
 within its reach   .........:::::.........        .........~~~~~.........
                    .......oo@@@@@oo.......        .......~~~~~~~~~.......
 The band           .....oooo@@@@@oooo.....        .....~~~~~~~~~~~~~.....
                    .......oo@@@@@oo.......        .......~~~~~~~~~.......
 Below the band,    .........:::::.........        .........~~~~~.........
 within its reach   .........:::::.........        .........~~~~~.........
 Beyond its reach   .......................        .......................

 @  The cell: Its footprint through its band       .  The slice's haze
 o  Its drop-off in the plane                      ~  What the take leaves: The slice's haze
 :  Its light in depth, I₀(r/d)², out to its reach
```

*Figure 15.* The halo removal, in a side view of one cell.

The same law gives the depth check, a law check of one space. It asks whether a brighter taken cell lies above or below a candidate's brightest place, within the reach of the time point's brightest sane cell, and covers much of the candidate's footprint. If one does, the two may be one cell counted twice.

### 5.6 The Candidate Pool

Every take yields a candidate, an \<object> pulled out and not yet called. It carries what the structure knows of it:

1. Its footprint, its band, and its column before the take;
2. Its own light before the take, kept apart from the volume, and the voxels taken at each slice;
3. How it came out: its route (the first pass, the site search, reaching down or the last look), its round, the lenses that held it, the bodies over or under it, and whether its two depth readings agree.

How it came out is a physical fact, not bookkeeping: a nucleus resolved cleanly in a first pass and one found only beneath another are different objects. The vectors write it as a facet of the candidate's places. The pool is generous by design: the structure offers every region it can enclose, and the expert's calls and the memory settle which are cells (§7 to §9). Figure 16 shows the first candidates of a sparse plate, in the order taken.

![The Candidate Pool](figures/F10.png)

*Figure 16.* The candidate pool on a sparse plate: the first candidates taken, in order, each
drawn at its band's middle, the top of its hump, on one brightness scale for the whole time point.
Magenta: the candidate's outline; orange: the other taken cells whose band holds that slice; white
crosses edged in black: annotated nuclei within two slices, drawn for the reader. Each label gives
the slice the candidate is drawn at; the candidates run in the order taken, left to right, row by
row.

None of these rules is tuned to the count or to a score. What they leave open is typed residue: a dome link that splits a body, an object to settle in one space, a candidate that may be a cell counted twice. In §9 the memory bends these same borders, as peaks and valleys of resemblance to confirmed cases.

## 6. One Language: The Hypervectors

The structure measures every place of a time point many times over, and each reading speaks its own
units: a focus score, a depth in slices, a round, a median. We write them all in one language. Then any
two readings can be compared by one operation, any difference between them can be named, and each place
can carry every scale it belongs to. Here we establish **H2** (one exact language).

The vectors sit at the turn of the paper's loop: the structure fills them, and the memory and every
later step read them.

### 6.1 What One Place's Vector Holds

In plain terms, a place's vector is a ledger with one column for every answer every measurement can
give: a measurement ticks one column, and an \<object>'s profile is the tally of ticks over its places
(Figures 17 and 18). The machinery below makes that ledger exact and cheap.

Every place's ledger holds every scale the place belongs to, for the reason a strand of DNA can be
repaired (Kunkel and Erie, 2005). A strand corrects a mistake with information it alone does not hold:
its partner strand as a template, the cues that mark which strand to correct, the repair proteins, its
local environment, its structure from secondary to quaternary. Restricted to the primary strand, that
gain of information would be impossible. The information comes from outside the strand, and the energy
from elsewhere, so the apparent local gain breaks no law of physics. Likewise the structure around a
place supplies what its own reading lacks, and each scale is checked by the others.

The vector makes that information available; each question's reasoning must still use it. Any question
may read any scale, and each scale's evidence stays in its own banks, readable apart: a disagreement
between scales is kept, never pooled into one score that picks a winner (concurrence, §4.4).

A **hypervector**, or **vector**, is a long array cut into blocks. Each block is a **bank**, holding one
kind of reading, and every value a bank can hold has a row of its own, a column of the ledger. The rows
are exact Sylvester-Hadamard rows: any two different rows cancel exactly, so the values written in one
bank never blur into each other, and banks, being separate blocks, never touch (the carrier, §12.1). A
reading is written as a **digit**, −1, 0 or +1 against a fixed middle, or as a word, by lighting its
row. Writings add, and each still reads back exactly, so a vector is fully described by how often each
row was written. A **bundle** is such a sum, kept as whole-number row counts, and an \<object>'s
**profile** is the bundle of its places.

There is one vector per place of the flat picture, shared by the lenses: each writes its own facets
there, in banks of its own, as the composite does in the full vector. A **facet** is the part of a
place's vector written at one scale. The table says whether each is written only in the **full vector**,
which holds every facet at the three anchors, or also in the **cheap vector**, read from the raw picture
alone at any time point.

| Facet | What it holds | Written in |
|---|---|---|
| The voxel, in each lens | Its light above the camera's dark, counted in the camera's flicker; the depth in slices it shows; whether the lens holds a body there | Full, cheap |
| The dome link and the ring | The place's light and depth, written into the bank of its direction to its center (one of eight), and into the ring's bank under its band of distance from that center | Full |
| The 16 × 16 neighborhood, in each lens | The grid square holding the place, as it stood at the start of the round its cell came out in: median, variance, share not black, frequency (how often the light's digit rises and falls across it), its spread of digits, its share with no signal | Full, cheap |
| The lens | Its whole picture at the same moment: median, variance, share not black, light, how one-sided the light lies; the camera's dark at its depth; how clearly the lens stands there | Full, cheap |
| The plate | Whether it moves; the share stage 1 leaves not black; its light; read once, at the start of the movie | Full, cheap |
| The lenses' conversation | How many lenses at near depths hold the place; whether they count it as one cell, disagree, or hold it alone; a body over or under it at another depth; the gap in slices | Full |
| How its cell came out | The route (the first pass, the site search, reaching down, the last look); the round; the lenses; whether its depth readings agree; the humps down its column | Full |

Each surrounding facet brings in what the place alone cannot know. The lens and the plate give the place
its scene; they point, and never decide alone. The dome link carries the dome's territories into the
vector: every place of one dome points at one center, so which places belong together is kept without
being stored. The ring keeps a nucleus's bright center in its profile. No error in finding cells can
corrupt the neighborhood, since a square is where it is by definition, not where a cell was guessed to
be.

Together these facets place a cell in its **context**: the class a cell falls in by what its vector
says of its surroundings and of how it was found. Its classes are a sparse or crowded plate, moving
or still, light or dark signal, its route out of the rounds, and the direction to its center. The
vector holds what is known before a question is asked. The answer, such as how well a context's
cells resolve, is measured in teaching and kept beside it, per context (§11).

Figures 17 and 18 write one nucleus this way. It lies on a sparse plate at t/2, and the expert called it one
cell. The two lenses that stand within its depths read its places above their middle; the other two
stand far from its band, and their pictures hold most of its places black. Summed, its places' rows are
its profile.

![One Nucleus Written at Every Scale](figures/H2a.png)

*Figure 17.* One nucleus written at every scale, on a sparse plate at t/2; the expert called it
one cell. (A) Its light at the slice of the lens that drew it, its outline magenta, a white ring at
the bright center most of its places belong to. (B) The voxel: each place's light as one digit in
each lens's picture, blue below the static middle, gray at it, red above; a place written by its
cheap reading alone is pale, and a silent one blank. The two lenses that stand within its depths
keep every place and read it above their middle. The other two stand far from its band: their stage
1/2 throws out most of its places, and there each writes only its cheap reading (§6.3). The
composite, made once the round's first pass had taken the nucleus, holds over half of its places
black, and is silent there. (C) Its own voxels: each voxel's digit along its footprint's middle row
through its band, depth running down, the band's thirds marked. (D) The dome link and the ring, read
in the composite made at the start of the round the nucleus came out in: written only where it keeps
the place, blank where it holds it black. That composite gives each place to its nearest bright spot
in the plane, at any depth; spots above the nucleus's band own most of its footprint, so the link is
written at just under half its places. An arrow at each place that writes a link points to the
center that place belongs to (a black dot), over the four green rings of distance from it; most
point to the nucleus's own center, and along the upper edge they point up, to two bright spots
beyond it. (E) The 16 × 16 neighborhood: the Gradient lens's picture cut into its squares, each
tinted by the digit of its median. (F) The lens: its whole picture, and the digits of its readings. (G)
The plate, read once at the start of the movie: still or moving, its share not black, its light.

![The Lenses' Conversation, How Its Cell Came Out, and Its Profile](figures/H2a2.png)

*Figure 18.* The nucleus of Figure 17, its readings across the lenses and its profile. (A)
The lenses' conversation: how many lenses near its depth hold each place, what they counted it as,
and whether a body lies over or under it. (B) How its cell came out: its route, whether its depth
readings agree, and the digits of its round, its lenses, the bodies over or under it and its humps. (C)
Its profile, written under the rule of §6.3: every place's rows summed into one count table, one
line a bank and one entry a row, an entry's color deepening with the share of the nucleus's places
that write that row. No entry of the table means nucleus; the profile is all of them together.

### 6.2 The Digit, Against a Static Middle

Each measured quantity is written as one digit, below, at or above a fixed middle, because the questions
asked of it are categorical: a reading need only fall on the right side of a line. A middle that never
moves keeps every digit comparable across places, time points and movies. The digit thus has the shape
of learning in the classical sense (§7.1): a departure from the expected, written with which way it was
off.

The **static middle** is the fixed reference a metric's digit is written against, one for each metric
and lens, the same for every place and time. It is a low and a high edge: the digit is −1 below the low,
+1 above the high, and 0 between. It is set once, at the metric's terciles over the movies the system is
taught on, so the three digits are equally likely. It never moves per movie or per plate, and is never
chosen to separate confirmed cases. Nor is it stage 1's dark: a middle is the reference of a digit, a
dark the baseline of a black.

A digit lights one of three rows, so a bundle keeps how its places spread over the three: an object half
above and half below its middle is not confused with one entirely at it. "At the middle" is a written
row, distinct from a reading never made. The value itself is kept beside the digit: arithmetic runs on
values, comparison and recall on digits.

A digit holds about 1.58 bits: it is a squint. The loss sits in the lenses and the encoding (the
precision ladder, §12.4); bundling, decoding and comparing are whole-number arithmetic and lose nothing.
Few bits suffice because the space is constrained:
- The question is small. Cells barely move, so between anchors it asks only where a known cell went,
  among the places its motion allows.
- It is asked as a delta. The prediction carries the known motion, so a digit need only say whether the
  light is still there, moved a little aside, or not there (the look, §11.2).
- Sources combine. A cell covers hundreds of places, each written in several facets. The limit is
  independence, not capacity, so the independence of views is measured before their agreement counts.
- Exclusion narrows the question: two cells never take one place, nothing merges, and time runs one way.
  A lawful exclusion also changes the meaning of what remains (the Monty Hall move, §4.6).

### 6.3 Silence and Black

A reading never made is not a low reading, and the language keeps the two apart. The **informational
zero** is a silent bank: "no reading here", which makes no claim. Unlike the digit 0, which says a
reading lay at its middle, it is left out of every comparison, dot product and norms alike, so it never
counts for or against.

Black is silence in the full analysis. Where a lens's stage 1/2 clears a place, that lens spends no full
analysis there; where the composite made at the start of the round holds a place black, no dome link or ring is written. Yet black is
not nothing. At an anchor such a place writes its **sparse** vector instead: its cheap readings and,
where the last look read something there, the last look's. Nothing can resolve a cell it is never shown.
So at an anchor the whole box is also written cheaply from the raw stack, and a cell every lens's stage
1/2 cleared can still be found by the search for missed cells (§10.1).

The absence is kept as well: the square, the picture and the plate count the place in their shares not
black. Each picture's black decides only for that picture.

### 6.4 Full, Sparse and Cheap

The heavy analysis runs at three time points, and the vectors follow it: the full vector where it ran,
the cheap vector wherever a raw picture exists, and like compared only with like.

| Vector | When it is written | What it holds |
|---|---|---|
| Full vector | t/3, t/2 and 2t/3, once the box is emptied; where a lens's stage 1/2 keeps the place | Every facet |
| Sparse | The same time points, where a lens's stage 1/2 throws the place out | Its cheap readings, and the last look's |
| Cheap vector | Any time point, from the raw picture alone | The voxel, neighborhood, lens and plate facets; the expensive banks silent |

The full vector is written from values the rounds already computed: writing it is counting, not
measuring again. Between the anchors no full analysis runs. Each time point gets the sparse treatment of
its raw picture, its cheap vector alone, written at the carried cells' bands for the look and wherever
the search for missed cells looks.

Full and cheap vectors share bank names, not sources. A full vector's cheap-named banks hold the
processed state: a taken cell's light as taken, black where stage 1 set it, the square and picture of
its round. A cheap vector's hold the raw picture. At an anchor each cell has both profiles, the cheap
one read from the raw picture over its own footprint through its band. Side by side, per context, they
are **the calibration**: the scale on which the looks between anchors, comparing cheap with cheap, judge
"the same" (§11.3).

Figure 19 sets the nucleus's two profiles side by side. Where both read, they read the same rows
except in three readings, and the banks only the whole pipeline writes are silent in the cheap one.

![A Cell's Full Profile Beside Its Cheap Profile](figures/H2b.png)

*Figure 19.* The nucleus of Figure 17: its full profile beside its cheap profile, bank by
bank. (A) What each profile reads. The processed state is the Gradient lens's picture in the round
the cell came out in, where the cell taken before it (orange) is out and its hole set to the haze.
The raw picture is the untouched slice, every cell's light still in it. (B) The two count tables on
shared lines, one line a bank, colored as in Figure 17. The full profile is written at the anchor
under the rule of §6.3, its dome link and ring read in the composite made at the start of the round
the cell came out in; the cheap profile is read from the raw picture alone, under the same bank
names. Between them, a bar shows how each bank's places are written: by the full analysis (dark), by
their cheap readings alone (pale), or not at all (dashed). At right, each bank's two lines compared.
Where both read, they read the same rows, except in three readings: whether a lens draws a body
there (no lens draws in the raw picture), the whole picture's variance (lower in the processed
picture, where the cells taken before it are out), and the lens's standing (not read in the raw
picture). The dashed frames are the cheap profile's silent banks: those only the whole pipeline
writes, those of the lenses that stand outside the cell's band, and, in this profile, the
composite's.

### 6.5 A Profile Is a Bundle

An \<object>'s profile is the bundle of its places. One arithmetic serves every scale, because a bundle
of bundles is a bundle: a cell bundles its places, and what the analyses said at a candidate's place is
bundled alike. A bundle is exact, independent of order, and undone by subtraction.

A profile holds, for every metric of every facet, how many of the \<object>'s places lie below, at and
above the middle, and for every word how many places say it. A cell's full profile also bundles its own
voxels through its band, keeping how its light falls through depth as the ring keeps how it falls from
the center. Where each place lies is kept beside the profile: the footprint, with each place's digits
and values. A confirmed case is kept as its own bundle, never added to another.

### 6.6 One Comparison, and a Difference Named

One language needs one comparison: to combine two analyses is to write both and read both banks, with no
rule for setting one lens's units against another's.

The **cosine** is the one comparison: the cosine of two profiles' row counts, over only the banks a
question reads. For tallies like these, it is 1 when two profiles hold the same proportions and 0 when
they share no column. Since the rows are exactly orthogonal, it is exactly the cosine of the two
vectors, taken in whole numbers under one contract (§12.2). It serves recognition, the search for missed
cells, the look, and recall from every memory.

A question reads the banks of the readings it is about, at any scale, named before the run it judges in
the **layout**, the versioned arrangement of banks, metrics and rows. Figure 20's question, about an
object's appearance, reads its own voxels, its dome link and its ring. The look, which asks where a
carried cell's light now is, reads every scale the cell's cheap profile carries. No bank carries a
weight, and none is chosen because it separates confirmed cases.

The writing has an exact inverse, so where two profiles differ is named: this bank, this metric, so many
more places below the middle. The difference is a sentence, not an index. It names the candidate for a
near miss's one difference, and whether that difference marks the failure is settled over the cases
(§7.6).

Figure 20 sets the nucleus beside an object the expert called noise. Their cosine says how near they
lie; the decode says what differs: the cell's own voxels lie mostly above their static middle, the
noise's mostly below.

![A Difference Decoded Into Named Readings](figures/H2c.png)

*Figure 20.* A difference decoded into named readings, on a sparse plate. (A) Two objects the
expert called, one cell (the nucleus of Figure 17) and noise, each in its light at the slice its
outline was drawn at. Beside each, its dome link, drawn where the composite made at the start of its
round keeps the place and blank where that composite holds it black: an arrow at every second such
place of the cell, and at every such place of the noise, points toward the center it belongs to
(black dots), over the green rings. (B) Their full profiles, written under the rule of §6.3, over
one question's banks, those of their own appearance (their own voxels, the dome link, the ring),
colored as in Figure 17, a dashed frame a bank a profile does not write. At right, how far apart
the two lie in each bank; below, their one cosine over these banks, which says how near they are and
never what differs. (C) The difference, named from the exact decode of the row counts. The cell's
own voxels lie mostly above their static middle, and the noise's mostly below. Of the places that
write a dome link, most of the noise's point north-east, to a bright spot beyond it, while the
cell's point every way, most of them to a center inside it. The cell is bright through the middle
and bottom thirds of its band, the noise dim in every third.

### 6.7 No Single Number Means Anything

No single number means anything here. The camera's dark, a brightness, a size and a focus score each
measure one thing correctly, and none alone says what anything is. Nor does a cosine. The target is not
a number but "cell", a statement about many small readings together: where the light stands, how it
falls from a center, which lenses hold it, what lies over and under it. So the representation decides
nothing. It makes the structure's readings and the memory's cases one kind of object, and meaning is
read by comparing a profile with confirmed cases, over a question's banks. Each agency then decides or
abstains.

The bridge under H2 is measured, never assumed: that the profiles keep the distinctions each question
needs (§1.4). Beside it, and measured the same way, the views' errors must be independent before their
agreement counts (§6.2). An exact code does not make an observation lossless. What an earlier black
silenced, no profile brings back, which is why the readings behind each such decision are kept.

## 7. The Unmasking: Bundles Are K-Lines and Censors

Here we establish the center of **H3** (the bundles are K-lines: taught once, fed back into seeing): the
bundles the one language needs to compare \<objects> are exactly the substrate of Minsky's K-lines and
censors. A **K-line** is a memory that re-creates what was active in a past success (Minsky, 1979). Once
an expert confirms a candidate, its bundle is the cue of a K-line, and the −1 digits of the expert's call
are remembered censors, memories that prevent an interpretation. The machinery of memory is already in
the representation, and the design meant it so: bundling is how its K-lines are stored. Learning in the
classical sense adds only what an expert confirms.

### 7.1 Bundling as Memory, and What Is Learned

A bundle is already a memory. A bundle of an \<object>, or of a region of one, records which readings were
present together over its places, at every scale they belong to, its surroundings included. Once an
expert confirms the candidate, the bundle records what was present in a success: what a K-line keeps.

A **case** is one remembered example of a typed object in a context. It keeps its bundle; the role
confirmed for it, its call; what was expected of it and how that was off, where it was; and its source,
what confirmed it. Each case is its own K-line, its bundle the cue. Cases of one answer are kept together
in a **bucket**, the store of confirmed cases for that answer. They are compared one by one, never summed
into one bundle per answer, since a sum would lose which readings occurred together in each case.

This is **learning** in the classical sense: a departure from the expected, recorded with how it was off,
in what context and about which role of which typed object, so that when the context recurs the mistake
is pre-empted. The memory holds the expectations that held, its K-lines, and the ways expectations
failed, its censors written from near misses. It is never a store of positions or data points, and never
fitted weights. What is learned concerns roles assigned to typed objects in a finite space of valid
contexts, within a fixed representation of the objects that matter physically and visually.

Recall works by nearness, but a case is not a data point. It keeps where it was taken only as its source,
and is recalled by its bundle, never by its place. Nor is it a sample to generalize over: it is one
confirmed expectation, or one confirmed departure, in its context, a precedent in Winston's sense.

The memory measures nothing itself: it reads the bundles the structure writes. The store described here,
of the agency of one real cell each (§10), is taught by the expert's calls. The clean-up reads it on each
candidate in the residual, drawing the line between noise and cell (§9), and so does **the cell
assignment**, which sorts what the clean-up keeps as one cell; several, N; or noise.

### 7.2 The Unmasking, Stated Operationally

The correspondence holds part by part. At its center, a K-line remembers methods, not answers: what it
brings back is no old verdict but a route to the structure's own tools, with the interpretation that
tells them what to do. Minsky illustrates the K-line with an image from Kenneth Haase. Smear red paint on
your hands before a repair, and every tool you use ends up marked; a wrench that did not fit should not
be (Minsky, 1986). The table sets the two side by side (Minsky, 1979).

| Minsky's K-line | Its counterpart here |
|---|---|
| Made when an idea or a solution is to be remembered | Made when an expert's call confirms a candidate, or corrects what was expected of it |
| Connected to the agents active at that moment | The case's bundle: every reading present over its places, at every scale |
| Activated by a situation that calls for it | The cosine of a present bundle with the case's, over only the banks the question reads |
| Induces a partial state resembling the one that made it | Reactivates the interpretation the case confirmed |
| Remembers methods, not answers | Routes the candidate to the procedure that interpretation calls for |
| The painted tools, and the wrench that did not fit | +1 digits, a positive memory; −1 digits, remembered censors of an interpretation |
| Prevention pointers, for which he saw "no easy way"; the detection of differences, crucial to Winston's learner, only sketched | The censor, stored with a confirmed bundle as its key; the exact decode, which names a difference |

**Recall** is the return of an interpretation by resemblance to a case. With the interpretation comes the
procedure it calls for:
- "One cell" admits the \<object> as one cell;
- "Several, N" sends it to **the Scissors**, the tool that parts a candidate into N cells at the most
  obvious places, under a contract of N that is never a quota: it makes no part the light will not give;
- "Noise" takes the whole candidate out of focus, a decision kept beside the case it rests on;
- In the clean-up, a remembered cell weighs against the noise interpretation of a place, and remembered
  noise draws the line between noise and cell in.

### 7.3 The Calls in Ternary

A **call** is an expert's word on a candidate or a region: one cell; several, N; noise;
not-cell-not-noise; or an abstention. The memory keeps each as a **ternary call**, one balanced-ternary
digit on each question the call speaks to. Calls must be ternary because evidence for (+1), evidence
against (−1) and no evidence (0) are three different things, and decide or abstain needs all three. On
the two questions the clean-up and the cell assignment ask, noise and cell, the calls write:

| Call | Noise | Cell |
|---|---|---|
| A cell | −1 | +1 |
| Noise | +1 | −1 |
| Not-cell-not-noise | −1 | 0 |
| An abstention | 0 | 0 |

One symbol per call cannot say "against noise, silent on cell". It turns not-noise into cell, or a
missing call into a negative claim, and so passes one off as the other.

The interrelation of the digits carries the finer logic: orthogonality constructed in a constrained
domain, not A or B, but A, its inversion, or something else entirely. A cell and noise are the first two,
each the other's inversion, which swaps +1 and −1 and leaves 0 fixed. Not-cell-not-noise is the third,
which neither of them can say: it shares the cell's digit on noise without the cell's claim. An expert
says it of the artifact of a cut in the wrong place, a region holding several cells, or a piece of one
cell that cuts into another: certainly not noise, and not one clean cell either. The orthogonality is a
property of the calls, not the exact orthogonality of the rows.

The negative is a fact of its own, given or confirmed by the expert, never inferred because a positive
match is missing. A call's 0 is silence, like a bank nothing read, not a reading at its static middle:
the notation is shared, the meaning is not. An abstention is kept among the calls; it never becomes a
case and teaches nothing.

### 7.4 Fuzzy Identification

**Fuzzy identification** is recognition by graded resemblance to confirmed cases, never by a threshold on
one number. It rests on the bridge under H3, Winston's precondition for reasoning by precedent, which he
called historical continuity: a situation similar to a past one generally leads to similar results
(Winston, 1980). The expert's calls establish that a resemblance is right.

It computes one cosine, over only the banks the question reads, between a present bundle and each case.
Figure 21 shows it on candidates the expert had not called, on a crowded plate.

![Recall on Candidates the Expert Had Not Called](figures/F12.png)

*Figure 21.* Recall on candidates the expert had not called, on a crowded plate, each drawn, and
its bundle written, on the slice where its outline was drawn, every cell's light still in it. (A)
Kept shapes the memory reads most clearly as cells. (B) Pieces it reads most clearly as noise. Each
label gives the shape's or the piece's size in places and two cosines of its bundle against the
stored cases of other objects: Noise, to the nearest stored noise case, and Cell, to the nearest
stored case on the cell side. The cosines, at 8 bits, chose what is shown and decided nothing.
Magenta outline: the candidate; magenta laid over the light: the shape kept; olive: a piece taken
off as noise; orange: the other taken cells at that slice. The expert confirmed nearly all of each
panel and left the rest unconfirmed.

In a drawing, each case acts with its digit on the question drawn. A +1 case is an **attractor**: a place
that resembles it is a valley the line takes in. A −1 case is a **repulsor**: a place that resembles it
is a peak the line avoids. A 0 does nothing. In the clean-up's drawing, each place goes with the nearer
of its nearest attractor and its nearest repulsor (§9.4). No level is set, since the drawing only
proposes, on a candidate already taken. Its regions decide, and the expert's calls stand over them, so a
place goes to its nearer case as a proposal, never as an answer.

Where recall assigns an answer, whether a case speaks at all is set by chance: its **trust radius**, the level a resemblance must clear, lies where the resemblances chance alone produces end, and it is set on real data. It says when a resemblance
is not an accident, never what a cell is. Every case within its trust radius speaks: at the cell
assignment, cell cases for "cell", noise cases against it, and not-cell-not-noise cases, 0 on cell, not
at all. The answer is assigned by concurrence (§10.2).

### 7.5 Censors: Negative Expertise

A **censor** is a memory or a law that prevents an interpretation. A *remembered censor* is a confirmed
case whose −1 digit pushes against an interpretation: what Minsky called negative expertise (Minsky,
1994). Much of what an expert knows is what not to do, and knowing it can shape a search before it
starts, more cheaply than generating and testing. In a constrained domain, what something is not tells
what another thing is (§3.6). So a remembered cell censors "noise", remembered noise censors "cell", and
not-cell-not-noise censors "noise" alone.

A *law-given censor* is a law that forbids outright, and it is absolute: the law that no two cells merge,
one consequence of memento mori (§2.3), forbids a merge. Remembered censors act in two operations, kept
apart. In a drawing, a remembered censor is a repulsor, weighed against the nearest attractor: never an
absolute veto. In recall that assigns an answer, a censor written from a near miss vetoes its one answer
within its trust radius, and nothing else.

Every remembered censor rests on a call, or on a failure its agency's own oracle has confirmed. A refusal
never writes one: not a take the structure refused, nor a place the clean-up leaves unresolved or
unassigned (§10.3).

### 7.6 Near Misses, and the Difference Named

A **near miss** is a confirmed failure that differs from a right answer in one significant, nameable way:
an expectation that failed in one respect. Winston's near miss may differ from its concept in a few
significant points at most (Winston, 1970). His learner could learn from one example when a single
difference localized the correction, and that case is our definition. A failure that differs in several
respects teaches nothing until failures like it share one consistent difference, and a refusal is never a
failure.

A near miss comes from an agency's own failure, confirmed by a signal independent of the memory. For the
agency of one real cell each, it is a call correcting the memory's proposal; for the agency of every cell,
a call of noise where it accepted a cell, the source of its censors. The near miss is read against the
K-line it recalled, and its one difference is named. What it writes sharpens the memory and is decided
against chance, in one of three forms:
1. Where the difference marks the failures, it becomes a censor of the answer that failed;
2. Where the successes of that K-line are the side that varies, a new K-line is written, claiming only the
   readings on which those successes agree: a **split K-line**. The original is kept and read through it,
   and the split changes what is claimed, never which banks a question reads;
3. Where neither holds, nothing is written, and the failures wait.

Suppose the memory recalls one cell for a candidate the expert calls noise, and the decode names one
difference: most of its places that write a dome link point to a bright spot beyond it, as in Figure 20. If failures like it
share that difference beyond chance, and the K-line's cells do not, it becomes a censor. If the K-line's
cells vary in it, since a cell's edge places can point beyond it too, a split K-line claims only what
they share.

The naming is what the exact substrate buys. Fitting Winston's learner into K-lines, Minsky found two
pieces wanting: a way to point to prevention, for which he saw no easy way, and a way to detect
differences, which he only sketched (Minsky, 1979). Here the exact decode names the difference between a
failure and the K-line it recalled: which reading differs, and what each says of it. The censor is stored
with the failure's bundle as its key. A code whose banks interfere, even slightly, says how far apart two
cases are, never exactly in what respect.

### 7.7 One Case and Its Recall

The correspondence is a reading of the representation, not an addition to it, and one case shows it whole
(Figure 22). Take the remembered region at left in row A. The clean-up draws it as noise on its
candidate, and the expert confirms it: an expectation that held. The case keeps the region's bundle, its
digits (+1 on noise, −1 on cell), what the drawing expected, and its source. The clean-up then draws a
region of another candidate, one the expert has not called, and compares it with the remembered regions.
This case is its nearest noise case; the nearest confirmed cell is farther away, so the region comes off.
In row B the comparison runs the other way: on a third candidate, a remembered cell, the nearer, keeps
the shape the clean-up drew. The remembered noise at right in that row is itself a departure: a region
the clean-up had kept. Resemblance decides, and the expert's call, independent of the memory, establishes
whether it decided rightly.

![One Case Beside What It Recalls](figures/H3.png)

*Figure 22.* One case beside what it recalls, on a crowded plate. Each row: in the middle, a
region of a candidate the expert had not called, which the clean-up decided; at left, the remembered
region it stands nearest, a case the expert confirmed; at right, the nearest remembered region on
the other side. Each tile shows its object's light at the slice its outline was drawn at, and each
bundle was written on that slice, every cell's light still in it. Olive: a region called noise;
magenta laid over the light: a region called a cell; a magenta outline: the whole candidate. Each
line carries the cosine of the region's bundle with the case's, over the banks of their own
appearance (their own voxels, the dome link, the ring), never with a region of its own object; the
heavier line is the nearer. The cosines are shown at 8 bits; the clean-up decides by the same
nearer-case rule in whole numbers. (A) A noise piece, nearer a remembered noise region than any
remembered region on the side that keeps: it comes off. (B) The shape the clean-up kept on another
candidate, nearer a remembered cell than any remembered noise: it stays. Shown both afterward, the
expert agreed with each.

The cue, the recalled interpretation, the routed procedure, the censor and the named difference are each
an operation the language already performs: a bundle, a cosine over a question's banks, a digit's sign,
an exact decode. Memory adds only what the structure cannot supply itself: the call, what was expected of
the case and how that was off, and its source. With them, what an expert confirmed of other objects bears
on this one where their contexts resemble. Classical AI is the natural reading of the representation.

## 8. Teaching Once: The Buckets

Here we establish the teaching part of **H3** (the bundles are K-lines: taught once, fed back into seeing). We show
how an expert's calls teach a memory that then routes candidates by itself. And we argue why a few hours of calls
suffice, on a few dozen examples of what a cell looks like and of what is noise or wrong.

The structure knows the laws of its domain, not how one kind of image looks. It pulls candidates out of a time point
but cannot say whether one is one nucleus, several pressed into one outline, or light that belongs to no cell. That
is a judgment of meaning, and its oracle is an expert's visual reasoning. So an expert teaches it once for each kind
of image, and the memory keeps it as cases. We call this teaching **the buckets**, after the stores it fills.

The stores belong to the agency of one real cell each (§10), and come in two sets. The identity buckets (one cell;
several; noise) are read by the cell assignment, on whole candidates. The clean-up's buckets (cell; noise;
not-cell-not-noise) are read by the clean-up (§9), on regions of candidates.

### 8.1 The Structure Proposes; the Expert Calls

For each candidate the structure proposes a word, and the expert's call confirms it or corrects it. This is learning
in the classical sense: the proposed word is what the structure expected, and a correcting call records how it was
off. The structure cannot settle the word by itself, since its readings carry numbers and no number means anything
alone (§6.7). What a candidate is takes reasoning over the picture, with the same laws. A hump down the column, a
peak with a valley above and below, signals a cell. Light that a brighter cell above or below explains by the
inverse-square law is that cell's halo. A candidate made of it is one taken before or with that cell, and the depth
check of one space flags it (§5.5). The readings support a word; the expert's call, an independent signal,
establishes it.

Teaching starts from a sparse time point and a crowded one, each with its emptied box checked by
eye. The emptied box comes first because a memory can only be taught about what it is shown: where
the box is empty, every cell-shaped signal is among the candidates. Both plates are taught because
their candidates pose different questions. On a crowded plate a clump comes out whole, since nothing
is parted before the take (§4.3), and one cell can be taken twice. On a sparse plate one large cell
can pass for a clump. Every case keeps its plate's kind as its context.

Each candidate is read in several ways, each measuring one thing. Its own light gives how many bright centers it
holds, the humps down its column, and its resemblance to confirmed cases. Its outline gives its area and its shape.
The other lenses say whether one at a near depth drew it as several bodies. While teaching, the annotated nuclei it
holds mean at least as many cells. Readings of one light are not independent, so they count by these four families.
A word needs the families' concurrence, as a take does at the commit (§4.5). A reading that cannot read abstains,
and never counts against. The words need:

1. One cell: at least two families for it, and none against;
2. Several, N: at least two families agreeing on N;
3. Noise, on a whole candidate: a structural reading (no bright center standing above its valley; narrower than a
   cell; or bright but tiny) together with resemblance to confirmed noise, never resemblance alone.

Where the families agree, the word is plain. Where they disagree, the candidate is hard, and what closer reading
does not settle goes to the expert.

The expert sees candidates on a **teaching sheet**, one for each proposed word and one for the hard ones, and
answers in three words: one cell; several, N, which gives the Scissors its contract; or noise. An abstention is
kept, and teaches nothing. Every other call becomes a case, its own K-line: the candidate's bundle, the call, the
word proposed and, where the call corrected it, how it was off, the context and the source.

Figure 23 shows two teaching sheets of a sparse plate. In panel A the readings word each candidate one cell, and the
picture shows why: a closed outline of a sane shape around one bright center, and in the side view a single hump of
light down the column. In panel B they word each candidate noise: a small, ragged outline with no bright center of its
own, and no hump. Some sit alone on a dark ground; others lie in the gaps between taken cells. The expert confirmed
both sheets.

![Teaching Sheets of a Sparse Plate](figures/F11.png)

*Figure 23.* Teaching sheets of a sparse plate. (A) Candidates the structure's readings word one
cell. (B) Candidates they word noise. Each candidate is drawn at the slice of its brightest place
(left) beside the side view through that place, depth running down (right). Magenta: the candidate,
through its band in the side view; orange: every other taken cell crossing the view; green cross:
its brightest place; white cross edged in black: an annotated nucleus. Each tile is labeled with the
slice it is drawn at, and each side view with the slices it spans. The expert confirmed both sheets.

### 8.2 Cosine Takes the Easy Half

Once each bucket holds clean cases, resemblance proposes, and the expert's time goes to the hardest candidates.
Resemblance may propose at all by Winston's precondition: similar situations generally lead to similar results. The
first cases are chosen for certainty rather than coverage. Then every candidate the expert has not called is
compared with every case, one by one, by the cosine over the banks its question reads. It goes on the teaching sheet
of the answer its nearest case gives, the most similar first.

The same teaching fills the clean-up's buckets. There is a sheet for the clearest of each answer, and one for the
messiest, where resemblance to confirmed noise and to confirmed cases against noise nearly ties. On the sheets of
the clearest noise and the clearest cells (Figure 21), the expert confirmed nearly all that resemblance proposed,
and left the rest unconfirmed. Resemblance takes the easy half at the cost of a glance.

The hardest calls are worth the most. Easy cases sit near the middle of an answer, where the memory already reaches.
A messy case at the edge, a very weak cell or blur where the light of two cells adds up, fixes where the line
between two answers runs. A call that corrects a proposal is a confirmed failure of the memory. It becomes a case of
the right answer, and, where its one difference from the case that proposed it can be named, a near miss that
sharpens the memory.

Few cases suffice because the space is constrained. A case is a whole profile, not one number: its
places carry every scale they belong to (§6.1), so the cell's surroundings come with it. The cells
of one kind of image resemble each other, most of all on a crowded plate, where they are pressed
into similar shapes with a tail of odd ones on either side. And one call writes a digit on every
question it bears on.

Nothing is tuned to agree with the expert. Every value a reading is tested against is written down before the run it
judges. Agreement between a proposal and a call is a consistency check, never a score to raise.

### 8.3 A Call Follows Its Object by Place

A call is about what is at a place on the plate, so it follows its object when the candidates change. The cells at a
place are the same whatever outline a candidate draws around them. And the candidates do change: the clean-up
redraws each one on the residual before the cell assignment sorts it.

A cleaned candidate is a candidate's kept shape, what the clean-up keeps of it. For each called candidate, we find
the cleaned candidate that holds most of its voxels. That one is the call's **successor**: the candidate itself, or
another that took its material. The call goes to its successor, whose bundle is written again over what it now
keeps, since the old bundle describes a candidate that no longer exists. A region's call follows its place the same
way, and the clean-up's cases are written in the residual, where it reads the candidates. Three kinds of call carry
by rules of their own:

1. A call of several carries its N only where those cells still are;
2. A call with no clear successor goes back to the expert, who rules on it from pictures and may leave the number of
   cells open;
3. A call that confirms only part of an outline, such as half of a dumbbell, waits until that part is drawn.

Every call is accounted for, and the old shapes, bundles and calls are kept. Calls made before the clean-up also
bring cases a cleaned set alone would never raise: a corpus more robust to variation.

### 8.4 Provenance, and a Memory That Routes Itself

The memory never confirms itself. Only a signal independent of it, the expert's call, confirms a case; anything else
would be circular. So a candidate is never compared with a case made from itself, since a case's cosine with itself
is one. And what the memory routes, or the clean-up draws by itself, is kept under a source of its own. It confirms
neither itself nor the cases that routed or drew it, and joins the buckets only at the expert's word.

Every case keeps its source: where it was taken (the movie, the time point, the run, its footprint and band); who
called it, on what evidence; the expert's words verbatim; and the teaching step that wrote it. Calls are never
overwritten; where two differ, the later stands beside the earlier.

Once the expert, looking at what the buckets propose, judges them discriminative, the memory routes
candidates by itself, by recall at the cell assignment. The baseline, the cases confirmed on the
sparse and the crowded time point, is used at scale only when the expert says it stands. It then
sorts the candidates of the other movies it is taught on, the teaching movies. What it cannot settle
is proposed and called the same way, and each cycle enlarges the set of cases the next proposes
from.

The cell bucket is one store, shared by the two sets, so the clean-up gains from every confirmed cell. Each is a
peak the noise line avoids, a remembered censor that weighs against noise. §9 shows what those peaks do, and §10.3
gives the rules of teaching common to every agency.

## 9. Seeing Better With Memory: The Clean-Up on the Residual

Here we establish the last clause of **H3** (the bundles are K-lines: taught once, fed back into seeing): the
memory moves the line the structure draws between noise and cell, and the line grows cleaner as cells are
confirmed. The structure draws each \<object> from laws alone, and most of what it draws is right. What it leaves
wrong is of a known kind. A candidate may carry noise at its edge, or light that belongs to another cell. That light
may be a neighbor's spread light inside the candidate's footprint, which the neighbor's take never enters (§5.5); a
fragment of a cell taken earlier in the loop; or a cell above or below it. The structure cannot settle such light
place by place, yet an expert sees it at a glance.

**The clean-up** carries that glance back into seeing. On each candidate it draws the line between noise and cell
by resemblance to cases the expert has confirmed, and the expert's calls establish that the line is right.

### 9.1 Where the Clean-Up Sits

The clean-up is the cell-and-noise part of the work of the agency of one real cell each (§10): a candidate that
holds a cell and some noise leaves it as the cell alone. The cell assignment that follows asks the rest of that
agency's question: is what remains one cell; several, N, sent to the Scissors; or noise? So noise has two senses
here. The clean-up's is material taken off a candidate; the cell assignment's is a whole candidate, taken out of
focus.

The clean-up receives every candidate of a time point resolved in full, once the rounds and the last look have
emptied the box. Each comes with its footprint, its band, its own light and how it came out, and with its
**drawing slice**, the slice at which its outline was drawn. The clean-up also receives the memory and, on a time
point being taught, the expert's calls on the candidates' regions, among them who owns a region two candidates
share. For each candidate it returns its **kept shape**, the places it keeps. Beside it go what came off as noise,
what another candidate owns, what no candidate owns, and the cases that decided each part. The kept shapes go to
the cell assignment.

The clean-up is neither the halo removal nor the last look's clearing. Those clear the volume; the clean-up
redraws each candidate.

### 9.2 On the Residual

The clean-up reads each candidate in the residual of the whole plate. In the raw picture a neighbor's light reads as
the candidate's own; in the residual it is gone, so the clean-up faces only what the structure could not explain.
This is the Wayfinder thesis (§4.6) turned on one candidate: a lawful removal, of cells taken with their light,
changes the meaning of what remains. On the candidate's drawing slice, every other taken cell is pulled out through
its band with its halo, its hole set to black, the slice's haze. The candidate's own light is left as it was.

Figure 24 shows two hard candidates, each called one cell, raw and in the residual. Above, a region that a
neighboring candidate had kept, and that the expert calls noise, is erased by the pull-out. Below, with its
neighbors' light removed, the cell stands brighter against a flat ground. Less signal overall gives a cleaner view,
as the squint does.

![Two Candidates, Raw and in the Residual](figures/F14.png)

*Figure 24.* Two candidates the expert called one cell, on a crowded plate, each raw and in the
residual. Each column: (A) its slice untouched, (B) the same slice with every other taken cell
pulled out through its band, with its drop-off in the plane, its places given the haze. Magenta
outline: the candidate; magenta laid over the light: what its clean-up keeps; green, then teal: the
cleaned candidates holding most of it; a gray hatch: its material left to no one; olive: its
material taken off as noise; orange: every other taken cell. Left (slice 61), a green region, drawn
to a neighboring candidate and called noise by the expert, is erased by the pull-out; the cell is
the whole magenta outline, its kept fill and its hatched part together. Right (slice 47), with its
neighbors' light removed, the cell stands out against a flat ground. Each column names the
candidate's slice, each row the view.

### 9.3 Three Buckets, Two to a Stage

The clean-up reads memory at two scales. At the scale of a place, its cases are whole candidates the expert
called, of three kinds: a cell, any call that is not noise; noise; and another cell's light, a candidate called
noise because its light was another cell's. At the scale of a region, its cases are regions of earlier drawings
the expert called, each bundled over its places in the residual: the clean-up's own buckets.

Each region call is a ternary call (§7.3), one digit on noise and one on cell. The clean-up draws the line that
encloses noise, the **noise line**, so each case acts by its digit on noise:

| Call | Digits (noise, cell) | In the noise line | Beyond the clean-up |
|---|---|---|---|
| Noise | (+1, −1) | Attractor: draws the line in | Repels cell at the cell assignment |
| A cell | (−1, +1) | Repulsor: pushes the line back | Shared with the identity buckets |
| Not-cell-not-noise | (−1, 0) | Repulsor: pushes the line back | 0 on cell: no part in the cell assignment |
| An abstention | (0, 0) | Silent: never a case | Kept with the calls |

The buckets are three, and they meet the clean-up as two sides: noise, and **non-noise**, every bucket whose digit
on noise is −1, read off the table. At the scale of a place, a whole candidate called several, N, which writes no
digits, stands with the cells'. The clean-up records its cell material and its not-cell-not-noise material apart,
and both stay in the kept shape.

### 9.4 The Drawing: Each Place Against Memory

The drawing proposes, and the regions decide. Each place goes with the remembered case it most resembles; each
piece this marks is then judged against confirmed regions. This is fuzzy identification, resting on Winston's
precondition (§7.4).

Each place has its vector on the drawing slice, in the residual. It is compared with every case by the cosine over
the banks the question reads, never with a case made from the candidate itself. Every bundle is first squinted to 8
bits (§12.4): its counts are kept no finer than the readings behind them support, since a decision drawn more
finely than its data is less correct, not more. Cases of a cell stand on one side, and cases of noise and of
another cell's light on the other. The nearer case decides:

1. Nearer a case of noise, a place is drawn as noise;
2. Nearer a case of another cell's light, it is drawn as cell light, and such places form the cell the drawing
   found;
3. Nearer a case of a cell, it is the candidate's own.

A tie, or a side where no case speaks, leaves the place unresolved. The drawing needs no level: it only proposes, on
a candidate the structure has already taken, so a place goes to its nearer case as a proposal, never as an answer.

The second rule is reading by exclusion (§3.6). A case of another cell's light was called noise only because its
light belonged to a cell other than its candidate's. It is still a cell's light, so on another candidate it is poor
at finding noise and good at finding the cell. The cell it finds is kept unless the regions say otherwise, and it
settles which of two candidates keeps a region both claim.

Then each connected piece of the noise drawn and of the cell found is bundled and compared once with the expert's
confirmed regions of other candidates: its nearest case of noise against its nearest of non-noise. Nearer noise,
the piece comes off. Nearer a cell, it is kept as cell; nearer not-cell-not-noise, it is kept and recorded apart;
unresolved, it is kept and shown. The expert's calls on the candidate's own regions stand over the comparison. This nearer-region rule settles only the clean-up's own question, noise or not, on one candidate; what the candidate is, one cell, several or noise, is assigned at the cell assignment, by concurrence (§10.2).
Each call that goes against it is a confirmed failure of what the drawing expected, and it teaches.

The two steps raise a second relief over the candidate's places, beside the relief of light that drew its border.
A place that resembles remembered cells more than remembered noise is a peak the noise line avoids. One that
resembles remembered noise more is a valley the line takes in. Figure 25 draws the line along one row of places.
A remembered cell thus weighs against the noise reading of each place, and wins wherever it is nearer than any
remembered noise: in a drawing a censor weighs and never vetoes (§7.5).

```
 THE LINE, along one row of places across a candidate, as the clean-up draws it

   Like remembered    |                      *********                         *****
   cells: A peak      |                   ***         ***                    **     **
                      |                ***               ***               **         **
   The even point    -+-----------*****---------------------**-----------**-------------**-------
                      |         **                            **       **                 **
   Like remembered    |**     **                                **   **                     *   *
   noise: A valley    |  *****                                    ***                        ***

   Each place:         .............#########################.............###############........
                                    ^                        ^            ^              ^
                       The line: Where the nearer remembered case changes side

   #  Kept: Its nearest remembered case is a cell (or not-cell-not-noise), so it stands on a
      peak the noise line avoids; a remembered cell here is a censor of "noise"
   .  Noise: Its nearest remembered case is noise, so it lies in a valley the line takes in
   The even point is where the nearest of each is equally near. The rules stay fixed; each
   confirmed case adds a peak or a valley, and the line moves with the memory.
```

*Figure 25.* The noise line along one row of places across a candidate, drawn schematically: each place goes to
the side of its nearer remembered case, so the set of places kept is the line.

### 9.5 Shared Places: The Ownership Map and the Kept Shape

Two \<objects> never occupy one space (§5.3), so a region two candidates hold has one owner. Another taken
candidate has a **claim** on the candidate's places where its band holds the candidate's drawing slice and its
footprint covers them. One **ownership map** settles each shared region and applies to both candidates of the
pair, so that neither deletes the other's evidence in turn. It gives the region, in order, to:

1. The owner the expert's call names, where there is one;
2. Else noise, where both sides that hold the region find it nearer noise;
3. Else no one, where the sides disagree, one finding it noise and the other not: a disagreement leaves the region
   **unassigned** unless the expert calls it;
4. Else the larger claim of a cell: the side where the cell its drawing found, meeting the region, is larger than
   the region;
5. Else no one: the region is unassigned.

The owner keeps the region, and it comes off the other candidate as another cell's material: a cell's, not noise.
A region given to noise, by both sides' finding, comes off both. Unassigned material is kept apart and shown, never made noise. The law
forbids two owners without naming one, and what it leaves open is information about an unsettled boundary.

The kept shape is the candidate's places less the noise, what another owns and what is unassigned. It is tidied as
any body is: its specks are cut and recorded apart, never taught as noise, since a speck is too small to argue
over, and its outline is pulled taut (§5.1). Both stay inside the footprint and never take a region another
candidate holds. The set of places kept is the line: a set bounded in space is enclosed by a line and described as
well by it. Bundled, it is a case the expert can confirm or reject.

Figure 26 shows the drawing at work on a crowded plate, on the untouched light of each
candidate's drawing slice. Take the second candidate in the top row of panel A, 240 places as taken.
A neighbor the structure also took (orange outline) crosses its lower right. Cases of another cell's
light, called noise on other candidates, find this candidate's cell: a round region covering most of
it (the magenta laid over the light). Where the neighbor's footprint crosses it, the cell found is
the larger claim, so the candidate keeps that part (hatched). Three places come off as noise
(olive), and the kept shape (the third tile) is nearly the whole candidate. Most of the clean single
cells of panel B lose little or nothing.

![The Clean-Up's Line](figures/F13.png)

*Figure 26.* The clean-up's line on a crowded plate, drawn on each candidate's drawing slice;
each tile shows the slice's untouched light. (A) Hard candidates, whose calls say they hold another
cell's light or share a part with another. (B) Clean single cells; most lose little or nothing. Each
candidate in three tiles: as taken (its magenta outline); the drawing; and what is kept (magenta
laid over the light). In the drawing, orange laid over the light is another cell's material, which
another candidate owns; magenta laid over the light, the cell found, kept, hatched where it is its
own material held against a neighbor; olive, noise taken off; a gray hatch, material left to no one.
Orange outlines: the other taken cells at that slice. Each candidate's labels give its places as
taken and the places kept, then the places its drawing takes off as noise and as another cell's.

### 9.6 A Loop That Cleans Itself

The clean-up grows cleaner with every confirmed cell, while its rules stay fixed. The rules come from the expert's reading of successive drawings and are fixed once a drawing is judged sound: they are part of the design, never a setting adjusted to agree with later calls. Afterward only the memory moves
the line, and no rule or level is tuned to a later call. The clean-up proposes, and the expert calls its regions.
Each call writes its digits into its bucket, with its source, and the next drawing reads the grown memory. Law
checks support the drawing, since no place is left with two owners; only the calls establish it.

While its noise bucket is built, the clean-up runs in rounds of its own, the kept shapes of one round the
candidates of the next. When the ownership map gives a shared region to another candidate, what remains may be
ragged, and the next round cleans it. Each round reads one fixed snapshot of the memory, so no round's proposal
teaches that round. They end when the places stop changing or start to repeat, and a guard on their number reports
unfinished work, never a success.

The memory needs plain cells before it can protect them. With a cell bucket made mostly of pieces of messy
candidates, it raises no peaks where plain cells are. The line then cuts into a dull single cell and breaks an
obvious one into fragments. So the teaching begins with plain cells the expert validates.

A confirmed cell is a remembered censor of noise. The cell bucket is shared with the identity buckets, so every
cell the expert confirms, hard ones among them (Figure 28), becomes one more peak the noise line avoids
(Figure 27). A dense library of cells is a dense library of censors against noise.

```
 The residual ─► Candidates ─► The clean-up ─► Kept shapes ─► The cell assignment
                                    ▲                          │ One cell: Admitted
                                    │                          │ Several, N: The Scissors
                                    │  A peak the noise line   │ Noise: Out of focus
                                    │  avoids                  │
                                    └───── The cell bucket ◄───┘ Every confirmed cell
```

*Figure 27.* The clean-up's loop: each confirmed cell returns to it as a peak.

![A Teaching Sheet of a Crowded Plate](figures/F11c.png)

*Figure 28.* A teaching sheet of a crowded plate: candidates the expert called one cell, hard
ones among them, each at the slice of its brightest place beside the side view through that place,
depth running down. Colors and labels as in Figure 23.

## 10. The Society of Agencies

The structure, with the memory's help, resolves most of what a time point shows. What neither settles is the
residue: the questions the structure leaves open, each typed by how it arose. A cell no round took; an object that
may hold several cells, or none; each cell's place away from the anchors; a division along a track. Here we
establish **H4** (a society learns only the residue): each kind of question has a learner of its own. The kinds
differ in what counts as right: no single sense of good or bad can reflect much of what goes on inside a society
of agencies (Minsky, 1986).

### 10.1 Four Agencies

Each learner is taught by a signal that does not depend on what it learns; one that did would teach it its own
errors. An **agency** is such a learner, with its own question, oracle, cases and measure: in Minsky's sense, a group
of parts considered for what it accomplishes as a whole (Minsky, 1986). Its **oracle** is the signal it is taught
against, clean for its question. The count depends on no extraction, an expert's call on no memory, a full
resolution on no following, and the annotation's divisions on nothing the division agency reads. An agency is
bounded by its check: one check against one clean signal makes one agency. The skills are the structure's; an
agency learns when to use which.

| Agency, and its question | Its oracle | Its stores | Where it acts | Its measure |
|---|---|---|---|---|
| Every cell: could a cell be here? | The count, in teaching only, with calls of noise for its censors | Combinations accepted as cells; censors from those calls | After the rounds at each anchor; where a cell goes missing or appears between anchors (§11.5) | The number of cells found against the count; every annotated cell inside a taken cell |
| One real cell each: one cell; several, N; or noise? | The expert's calls | Its identity buckets and the clean-up's | At taking; in the clean-up; at the cell assignment and the Scissors' parting | Identified, abstained and wrong, per kind of object |
| Position: where did this cell go, and how will such a cell err here? | Full resolutions of the teaching movies' time points, for the cells they resolve cleanly; in a run, the three anchors | Records of the jiggle and of carried places' errors; the guarantee's table; for identity, K-lines and censors | At every step of the movie | Within 7 µm or not, as the hosts' check (§2.4) asks, per context and span; the compute spent |
| Division: did it divide? | The divisions the annotation marks, with the expert's calls on what only looks like one | Chapter evidence and its arbiters (§11.6); division cases; censors from those calls | Along every cell's track | The trace from mother to daughters |

The structure's own tools already see most cells, and what they half-see is where the rest are. So the every-cell
agency's candidates are places the analyses half-saw and none ruled out, such as a faint body or a hump nothing
took. Each is written as its **combination**, one digit per analysis: +1 where it saw a cell, −1 where it saw
nothing, and 0 where it half-saw one, a reading at its middle and not silence (§6.3). Figure 7 shows such
evidence: how many lenses hold each place. Beside the combinations runs the search for missed cells: it matches
each taken cell's cheap profile against the cheap vector, written wherever the search looks, and proposes the
places that resemble one. Exclusion strikes first: a place a taken cell holds, light its optics explains, a place a
censor vetoes. What survives is taken and checked as any take is, then passed to the one-real-cell agency:
resemblance chooses where to try, never what a cell is.

The count is used only in teaching. It establishes how many, never which: it is the every-cell agency's oracle for
how many cells remain to find, and it supports, never establishes, any judgment about one object. Among the
candidates that pass, the best, ordered by recall against confirmed combinations, are accepted while the count asks
for more, each keeping "accepted by the count" as its kind. It is the one order by resemblance the design allows,
and only in teaching: the count adds and never trims, so nothing taken is removed to meet it and no level moves
(§4.8). It confirms no failure: a candidate it leaves untaken is unconfirmed, never noise. In a run, remembered
combinations, their censors and the search for missed cells choose what to try.

Figure 29 shows the one-real-cell agency, the memory the buckets teach, at work. This candidate was taken whole,
as every take is, and its readings proposed several, N. The expert called it two cells: an expectation that held,
kept as a case of several, N, the interpretation recall routes to the Scissors. The call answers this agency's
question and no other: whether the two are sisters, newly divided, is the division agency's, read along their
tracks.

![A Candidate in the Bucket for Several](figures/F17.png)

*Figure 29.* A candidate in the bucket for several, N, on a sparse plate: at the slice of its
brightest place (left), beside the side view through that place, depth running down (right).
Magenta: the candidate; orange: other taken cells; green cross: its brightest place. The tile is
labeled with its slice, and the side view with the slices it spans. Its readings proposed several
cells, and the expert called it two.

The position agency learns where the drift and the jiggle break. It keeps mostly **records**: measurements kept
under a profile or a context, such as how a context's cells jiggle and their carried places err. For identity it
holds K-lines and censors (§11.2).

The division agency's oracle is an expert's too: the annotation's divisions are the hosts' record of their nuclei's
lineages. So, as for any machine intelligence, the oracle behind every teaching signal is in the end a human
expert: here the expert's calls, the hosts' annotation and their estimate of the count. Even a full resolution
answers to them: agencies they taught make it, and the annotation measures it.

### 10.2 One Language, and Recall by Concurrence

The agencies meet only in the one language and the kept record of findings, and among them, as among the lenses
(§4.4), truth is assigned by concurrence. No one memory decides at once whether an object is a cell, whether it is
one, and whether it divides. Every case, censor and record is keyed in the same vectors, so one cell's profile is
readable by all four, each over the banks its question names.

In recall, the voices are the cases within their trust radii, and the censors from near misses, each vetoing its
one answer within its radius:
1. One answer standing is recalled;
2. Two or more are a disagreement, kept, and never broken by order, averaging or the strongest voice;
3. None is an abstention.

Either of the last two returns the question to the structure's own path: the less ambiguous viewpoint that the
principle of noncompromise, first formulated by Papert, seeks instead of a compromise (Minsky, 1979; Minsky, 1986).
Each agency decides or abstains (§4.8), answering only under proof. No agency is the pipeline, and no one score
grades the society. Figure 30 draws the society.

```
 The structure (§3 to §5) leaves a typed residue
                                  │
  ┌────────────────────┬──────────┴─────────┬───────────────────┐
  ▼                    ▼                    ▼                   ▼
  One real cell each ► Every cell ────────► Position ─────────► Division
  One cell; several,   Could a cell         Where did it go,    Did it divide?
  N; or noise?         be here?             how will it err?
  ▲ The expert's       ▲ The count, in      ▲ Full resolutions  ▲ The divisions the
    calls                teaching; calls      (anchors, in a run) annotation marks;
                         of noise                                 calls
  │                    │                    │                   │
  └────────────────────┴──────────┬─────────┴───────────────────┘
                                  ▼
 They meet in the one language (§6), where every store is keyed, and the kept record of findings
                                  │
 Truth by concurrence: One answer, recalled; two or more, a disagreement kept; none, an abstention

 ▲ The oracle each agency is taught against; behind every one, in the end, a human expert
 ► The order of teaching
```

*Figure 30.* The society of agencies, in the order they are taught.

### 10.3 The Rules of Teaching

An agency learns only from what its own oracle confirms. Learning in the classical sense is a departure from the
expected, kept with how it was off (§7.1), and only a signal independent of the memory can say it was off.
Four rules follow:
- *Each agency is taught from its own oracle,* in a **curriculum** of its own: only the cases its own check judges.
  One pooled set would blend contexts that answer differently, and every failure would differ in many respects, so
  no censor would form.
- *A confirmed failure teaches.* When a store answers wrongly and its agency's oracle confirms it (for the every-cell
  agency, a call of noise), the right answer becomes a case. The failure is read as a near miss (§7.6): it writes a
  censor, a split K-line, or nothing.
- *A refusal teaches nothing.* A refused take, an unresolved object or an unsettled step says the question was not
  resolved there, never that nothing is there. Kept as an unconfirmed finding, it writes no censor, which would
  stop the memory looking where the every-cell agency must.
- *No agency is taught by the cases it settled itself.* What a memory routes keeps a source of its own and confirms
  nothing, so every confirmed cell, and no routed one, is a peak in the clean-up.

The order of teaching follows what each agency consumes. The one-real-cell agency comes first, so that objects are
settled before the count asks for more: until the candidate of Figure 29 is known to hold two cells, the count
asks for a cell already there. The every-cell agency follows; then position, on the teaching movies' time points
resolved in full with those two acting; then division, on the tracks position makes.

### 10.4 Judged by the Course of Its Learning

An agency is judged by its **trajectory**, the course of its learning, never by one final number. What it learns is
its expectations getting better in the contexts it has seen, and only the course of its answers shows that. After
each step of teaching, on movies it was not taught on, dense and sparse, we read what it identified, abstained on
and got wrong, per kind of answer and never summed. Turning a wrong answer into an abstention is progress. Its
memory's change from step to step is read bank by bank, as a cell's profile is. A change that never settles is a
sign of an agency storing instances rather than forming rules, and the answer is more structure, not more memory.

A plateau calls for a decision with the expert: accept, teach further, or build the missing structure, the move of
the Wayfinder thesis made again on what stays hard. A moving number never chooses the next change by itself. No
agency is admitted by beating the run without it; that run is kept to show what the structure does alone.

### 10.5 What Supports, and What Establishes

Law checks support a judgment; an oracle establishes it, and only for its own question. This is H4's bridge. A law
check reads the output alone, so a wrong answer that breaks no law passes it. So the law checks of §2.6, run on
every agency's output, only support. The oracles establish: the count, how many cells remain to find; a call, what
an object is; a full resolution, where a cleanly resolved cell is; a division the annotation marks, that a cell
divided.

The society's gain is the work the structure no longer does: the rounds a remembered combination saves, and the
full resolutions a taught position agency spares (the Ephemeris move, §11.4).

## 11. Following: Identity First, Then Position

Once the system knows what each cell is, following it through time is cheap. A cell is a persistent \<object>
that barely moves, so the system gets each cell's position and measures the change (memento mori, §2.2). This is
**H4** (a society learns only the residue) in time: identity is resolved in full at three time points, and the
position and division agencies follow each cell from them. Laws carry each cell, anchors on both sides check
it, a cheap look at every step corrects it, and a bound says when to measure again.

### 11.1 Three Anchors, and the Laws Between Them

Between the anchors each cell is carried by the laws of its motion. A cell moves steadily, with its surroundings
or pushed by them, or by chance, a little. So a steady part carries it, and a random part bounds where to look.

Each cell taken at an anchor hands on its outline, its full and cheap profiles, and its context (§6). A cell is matched across the anchors first: carried from one anchor by the plate's drift and looked at every step, it lands in an outline at the next, which names it there (§11.5). Its two full positions then give the line between them. The anchors
sit inside the movie, and their pairings span two lengths, which tell a steady drift from a random wander (§3.4).

The steady part is **the static model**, which carries each cell forward from an anchor and backward, its shifts
reversed. Between two anchors a cell's predicted place lies on the line through its two full positions, corrected
by the shared motion. Outside them it moves by the plate's drift from the nearer anchor alone, so the tails are
fuzzier, never gaps. A still plate reads no motion, a moving plate its drift, a region moving apart its own.
Figure 31 shows why the line is needed. On a still plate, annotated nuclei move a little at every time point,
but steadily, so the plate's drift alone would leave them behind.

![The Three Anchors on a Still Plate, and the Annotated Nuclei's Paths](figures/F16.png)

*Figure 31.* The three anchors on a still plate, drawn for the reader from the annotation, in
teaching: the annotation's paths, never the system's tracks. Over the plate at t/2, seen from above,
each annotated nucleus is followed time point by time point from t/3 (lightest green dot) through
t/2 (middle green) to 2t/3 (darkest green); the thin line is its path, its color only telling the
nuclei apart. Each moves a little at every time point, but steadily, so its path between the anchors
is long, while the whole field's measured shift between them, drawn from the picture's middle, is
short: the plate is still. The shift from t/2 to 2t/3 is drawn in the darkest green; the shorter one
from t/3 to t/2, in the middle green, lies beneath it. Between the anchors such a cell is carried on
the line through its two full positions.

The random part is the jiggle, kept per context as a record of the moves cells made between consecutive time
points resolved in full in teaching. Drawn from it by Monte Carlo and compounded since the anchor, the moves give
the cell's **envelope**, where it can be. The envelope decides nothing; it sizes the look. A carry from one side
also adds the line's own error, which grows with the span, while the jiggle grows only with its square root.

### 11.2 The Look, at Every Step

At each step, forward or backward, **the look** asks a small question: where did a known cell's light go, among
the few places its motion allows? The prediction carries the known motion, so a cheap reading answers it.

The look reads the next time point's cheap vector at the carried cells' bands, since a cell keeps its depth. It
looks far on a sparse plate and near on a crowded one, where looking far would find another cell. Places other
cells hold are never searched, since two cells cannot occupy one space. The cell's cheap profile is compared, by
the one cosine over every scale it carries, with each **window**: its own footprint, through its band, moved to
one candidate place inside its envelope. Each window's counts come cheaply from running sums (§12.3). The shift is
the offset where the profile matches best, and the look answers still there, moved a little aside, or not there.

Figure 32 shows one look's geometry on a sparse plate, a step after the anchor at t/3. The prediction falls on
the cell's light, a little off its center. The light is found a short step aside, where the annotated nucleus
lies.

![One Look](figures/F15.png)

*Figure 32.* One look, on a sparse plate, one time point after the anchor at t/3, at slice 61. A
cell resolved at the anchor is carried one time point forward by its region's prior. (A) The slice
around its predicted place (ring), and the square the look searches, 16 places (6.5 µm) to each side
(dashed). The look finds the cell's light 4.4 µm from the prediction (small circle); the annotated
nucleus there (cross), drawn for the reader, lies 1.1 µm from where the light is found and 5.3 µm
from the prediction. (B) The cell as resolved at the anchor, slice 61, outlined in magenta: the
light the look searches for. The picture shows the look's geometry (prediction, search and the place
found), not the comparison of windows.

Two cells that look alike are told apart by the structure around them. Which cheap readings resolve identity in
each context is what the position agency learns. It holds them as remembered, named differences, never as
weights: K-lines of matches that held, and censors from near misses, each naming the readings in which a failed
match differed from a right one (§7.6). What it learns changes what a match may claim, never which banks the look
reads (§6.6).

The place found is corrected at once by the position agency's error record: how such places erred in teaching,
in the cell's context. Four checks then read the corrected place:
1. Its shift stays within the jiggle of its neighbors' shared motion;
2. Its light, moved by the shift, nearly coincides with the light at t + 1;
3. A place two cells contest is narrowed by exclusion, then by each look's own evidence, never by which cell it
   resembles more; a contest left open settles neither;
4. Its cheap readings are not very far off those at its anchor.

A step that passes settles the cell's place: the prediction plus the corrected shift, a modeled position, never a
measurement. A step that fails keeps the cell's identity at its prediction, since a cell does not vanish, and
hands that place to the every-cell and one-real-cell agencies. It is a refusal, and teaches nothing; in teaching,
a failure that a full resolution confirms does.

### 11.3 The Squint Over Time

The squint works in time too: between anchors each step compares only cheap, sparse dimensions, like with like.
Its question, whether this is still the same cell a little aside, is categorical, and a reduced signal answers it
more cleanly and cheaply. The full profile informs the look through the cell's context and the calibration (§6.4).

Three quantities are kept apart, each with its own consumer:
- The physical shift, the best-matching offset: a cosine says how alike two profiles are, not how far one moved,
  so the place kept is built from the offset, never from the cosine;
- The change in the cell's readings against those at its anchor, read by the look's last check and, along the
  cell's **track**, its profiles in order, by the division agency;
- The calibration: at each anchor, per context, the relation between cells' full and cheap profiles, the scale
  on which the looks judge "the same" and the last check judges what is very far off.

So the full vector, which holds every scale, is the deep oracle: its heavy analysis, made three times, is grounded
at every step in what is cheaply seen. Figure 33 draws it on a short track between anchors.

```
Time ->   t/3                           t/2                           2t/3
          |                             |                             |
Vector:   Full + cheap  c   c   c   c   Full + cheap  c   c   c   c   Full + cheap
Carry:    |-- Forward: Predict, look -->|-- Forward: Predict, look -->|
          |<-- Backward: Predict, look -|<-- Backward: Predict, look -|
Anchor:   The calibration, per context: Full profiles beside cheap = the scale of "the same"
Step:     Cheap profile at t  vs  cheap vector at t+1  ->  The shift (where it matches best)
                                                       ->  The change in its readings
          The full profile informs each look through context and calibration
          c = A cheap vector from the raw picture; for the look, at the carried cells' bands
```

*Figure 33.* The squint over time, on a short track between anchors: full and cheap vectors at each
anchor, cheap ones between, and each step comparing cheap with cheap.

### 11.4 The Guarantee, and the Ephemeris Move

A carried place is modeled, never measured, so it needs a bound; where the bound fails, the system measures again.
**The guarantee** bounds the mean distance between a context's carried places and their cells at a span, as the
sum of two errors. It certifies no one cell's place.

G is the resolution's own error, measured in teaching against the annotation and kept per context as a bound on
its mean. T is the error time adds after the last anchor. It is measured on teaching movies resolved in full at
many time points, where each carried place's distance from the full resolution of its moment is kept by context
and span. Each entry is a measured mean with its empirical-Bernstein bound: a bound on a mean computed from the
observed values and their spread (Waudby-Smith and Ramdas, 2024).

In a run, an anytime empirical-Bernstein sequence, which holds with a stated confidence however often it is read,
follows the movie's own evidence. That evidence is where two determinations of a place meet, the steps left
unsettled, and shifts the jiggle does not explain. Where teaching has no entry for a span, where that evidence
leaves teaching's range, or where G + T approaches 7 µm, the time point is resolved in full. The 7 µm is the
distance within which the hosts' check (§2.4) matches a position to an annotated nucleus. It covers both errors,
and is not how far a look searches.

That resolution is **the Ephemeris move**, after the astronomer's ephemeris, a table of predicted positions that
observation re-grounds. It never starts blind: each carried cell is looked for first where its prediction puts
it, its difference kept, and the rounds resolve the rest. The time point becomes a new anchor. The design expects
the three anchors to suffice.

### 11.5 Identity Across the Anchors, and the Sandwich

Between t/3 and 2t/3 every cell is carried from both sides, and two sides whose independence is measured make a
persisting error exponentially unlikely. Each side carries its own place and bound, and the place kept is the side
with the smaller bound, not the nearer. The distance between the sides bounds the sum of their errors from below.
A large distance can show that a bound has failed; a small one never shows that it holds, since two carries can
agree on the same wrong neighbor. Their agreement is a law check, which supports (§2.6); only a full measurement
establishes. At an anchor a carried cell is the same nucleus when its carried place falls inside a taken cell's
outline; inside none, or two, the match abstains, a finding.

Physics and biology act as compilers that reject inconsistent logic: nothing appears from nowhere or vanishes
without a cause (§2.3). So a cell seen at both anchors is there at every step between. We call this structural
prior of logic **the sandwich**, after the sandwich, or squeeze, theorem of calculus: a quantity held between two
that agree must agree with them. It is neither a statement of identity nor a rule for admitting a cell. A cell
missing at a step, or appearing, is an inconsistency, and stopping there is a violation. The system must find
which of four answers holds (Figure 34):
- It was missed: look harder, with the cell's own cheap profile from where it was plain, and check again anything
  cell-shaped nearby that was called noise;
- It divided: find the parent, and trace the lineage;
- It died;
- It crossed the field's edge: a cell that reaches the edge left; it did not die.

The system states an answer only when that answer is shown, and never infers "it died" by ruling out the others.
Where no answer is shown, it abstains, and the inconsistency stays open and recorded. That is not giving up: the
law still says the answer is one of the four.

```
t/3, an anchor                  t/2, an anchor
    |                               |
    o---o---o---o---o---o---o---o---o   At both: At every step
    o---o---o---o   .   .   .   .   .   Missing    } An inconsistency,
    .   .   .   .   o---o---o---o---o   Appearing  } never left so
The compiler accepts only an answer that is shown:
  Missed    Look harder; check again what is cell-shaped nearby and was called noise
  Divided   Find the parent; trace the lineage: Her track ends, two daughters' begin
  Died
  Crossed   The field's edge: It entered, or it left
  None shown: Abstain; the inconsistency stays open and recorded
o Seen    . Not seen
```

*Figure 34.* The sandwich, a compiler of logic: a cell missing or appearing, its four answers, each stated
only when shown, and the abstention where none is.

### 11.6 Division Along a Track, and the No-Merge Law

Division is read along every cell's track, never at one time point. A dividing nucleus condenses, pinches in two
and becomes two daughters moving apart along mirrored paths: each sign is small, and the story is unmistakable.
At the anchors the full profile can show a second center; at every step the cheap one shows the cell's light and
spread, and a gap at its center.

At each read, a chapter reader weighs the evidence for four chapters. They are named for stages of division but
set by time around the split: prophase, a few time points before the mother's last; anaphase, her last two;
telophase, the daughters' first two; and interphase, a continuing cell. For each row of the cell's readings and
each chapter, it consults two counts kept in teaching, from divisions the annotation confirms. One is how often
the row is lit at that chapter's time points, the other how often at the same offsets in continuing cells. The
logarithm of their ratio is the weight of evidence of Turing and Good (Good, 1950), a measure of what was seen,
never a setting. Nothing in the reader is searched: no row, offset or count is chosen or changed by how well
divisions are then read, which would make it a fitted combiner. Read together per chapter, the counts give the
story its lean.

**The dean**, the reader that decides whether a cell divides, aligns the track against two stories, division and
continuation, allowing gaps (Gotoh, 1982). It reads which fits and by what margin; a moment not read is silent,
and a track too sparse abstains. A strong but imprecise sign only leans: however wide its margin, it commits
nothing alone. A weak but precise sign, an arbiter named with the expert, is rare and clean: where it shows, it
fixes that moment's chapter, and where it does not, it weighs nothing. Beside the story, the relation reader reads
a mother and a candidate pair of daughters by their mirror symmetry, separation and balance of mass. It keeps or
strikes each pairing on its own, and a division is written only by concurrence: where the dean reads one and
exactly one pairing survives.

Over all of them stands the no-merge law, one consequence of memento mori and a law-given censor (§7.5): no cell
has two pasts. One object at an anchor and two at the next is read for division first; two becoming one never is,
and goes to the one-real-cell agency. A confirmed division ends the mother's track and begins her daughters'
tracks, linked to her, each from its birth. The division agency's memory stands beside these readers: its cases,
and its censors from calls on what only looks like a division, such as touching nuclei that are not sisters. It
never decides alone.

## 12. Methods: The Mechanics

The representation and the memory are exact, and their cost is part of their design. Exactness lets a
difference be named and a kept value be trusted. So every loss is taken on purpose, in the lenses and
the digit, and none in the arithmetic on vectors. Here we give the machinery beneath H2 to H4: how
vectors are held, compared and stored, and how a run's work is organized.

### 12.1 The Carrier

The **carrier** is the arithmetic object the vectors are written in. It departs from textbook
hyperdimensional computing (Kanerva, 2009) wherever exactness is at stake, since a memory that keeps how
a case was off must read its codes back exactly.

| | Textbook hyperdimensional computing | The carrier |
|---|---|---|
| Codes | Dense random ±1 vectors, orthogonal only on average | Sylvester-Hadamard rows in a seeded order, orthogonal exactly |
| A value | A scalar carried in the vector | A digit lighting one row; the value kept beside it |
| A zero | No information | A silent bank: a fact that makes no claim and costs no arithmetic |
| Reading back | An approximate similarity | An exact decode of every count |
| Precision | Floating-point cosines | Whole numbers throughout |

Each bank is 512 dimensions wide, its rows those of the Sylvester-Hadamard matrix
H[i, j] = (−1)^popcount(i AND j), in an order permuted by a generator seeded with the bank's number.
Two different rows agree in exactly half their dimensions, as Figure 35 shows for eight, so
H Hᵀ = 512 I. Rows cancel exactly, so values written in one bank never blur. Banks occupy separate
dimensions, so they never interfere.

```
   Row 0   ++++++++     H[i, j] = (-1)^popcount(i AND j), j from 0 to 7
   Row 1   +-+-+-+-
   Row 2   ++--++--     Any two rows agree in 4 places and differ in 4: Their product sums to 0
   Row 3   +--++--+
   Row 4   ++++----
   Row 5   +-+--+-+
   Row 6   ++----++
   Row 7   +--+-++-
```

*Figure 35.* One bank's rows, drawn 8 wide.

The carrier holds as many banks as its layout needs, so every place can carry every scale it belongs
to, for the reason DNA's repair gives (§6.1).

A bundle has two exact forms. Its **count table** holds how many times each row of each bank was
written. Its vector is the sum of those rows, whole numbers stored in 32 bits and summed in 64. The
**exact decode** turns the vector back into the table: a bank's vector times the bank's rows is 512
times each row's count. Counts add in any order and are undone exactly by subtraction.

Within a bank, hᵢ · hⱼ is 512 when i = j and 0 otherwise. So for v = Σ cᵢhᵢ and w = Σ dᵢhᵢ,
v · w = 512 Σ cᵢdᵢ and ‖v‖² = 512 Σ cᵢ². The cosine of two vectors is therefore the cosine of their
count tables, over one bank or many.

For one comparison, then, the vector adds nothing a count table lacks. What it adds is one kind of
object for every table in the system. Every reading, at every scale and from every analysis, has an
exact orthogonal address. Any number of writings superpose and read back exactly, and a bundle of
bundles is a bundle. So no table needs a schema of its own to meet another.

The vector's **packed signs**, kept in two bit planes a bank and compared by exclusive-or and a count of
set bits, give every store a small fixed-width signature to hold and ship. They are the counts' squint:
they may order a scan, but never drop a case, since agreement of signs is no bound on the cosine of
counts. For two rows h₁ and h₂ of a bank, u = 3h₁ + 2h₂ and v = 2h₁ + 3h₂ have a count cosine of 12/13.
Yet u takes h₁'s sign in every dimension and v takes h₂'s, so their signs' cosine is 0.

The carrier's construction and comparison carry a versioned name, so a stored memory says which carrier
wrote it. The layout is versioned too, and profiles of different layouts are never compared.

### 12.2 Whole Numbers, and the One Comparison

Every comparison is one cosine of count tables, computed in whole numbers. Whole numbers give a
comparison one answer on every machine and in every order of summation, so no decision rests on a
rounding. A cosine is tested against a **level**, a ratio of two whole numbers written down before the
run it judges, or set beside another to say which is nearer.

One contract serves every comparison: one cosine over every row of every bank the question names (§6.6)
and both sides speak in. A bank either side leaves silent is out of the dot product and both norms, and
a bank the question does not name is neither read nor paid for. It is never a cosine per bank,
averaged, which would give each bank one vote whatever it holds, and change its answers with how rows
are grouped into banks.

In whole numbers:
1. Counts are never negative, so a cosine reaches the level a/b exactly when
   b² · dot² ≥ a² · ‖u‖² · ‖v‖². Every term is a whole number, widened wherever it could leave 64 bits.
2. Of two pairs, the first is nearer when dot₁² · ‖u₂‖² · ‖v₂‖² > dot₂² · ‖u₁‖² · ‖v₁‖², and equality
   is a tie.

A comparison answers in words: "reaches", "short" or "silent", so a pair with nothing to compare
abstains rather than fails. Nearness compared so lets each place of an object find its nearest case in
a store, and each look its best window. A scan may drop a case only where an exact bound proves that it
cannot reach the level.

### 12.3 Windows by Running Sums

The look compares a carried cell with the cell itself, moved. A window is the cell's own footprint,
through its band, moved to one candidate place inside its envelope: the same object in another place,
so like is compared with like. At the cell's own place, the window is the cell's cheap profile (§6.4)
exactly. A footprint-sized square would hold its neighbors' light in its corners. The search for
missed cells moves each taken cell's footprint the same way.

Running sums make a window cheap. A footprint is kept as its runs, each maximal stretch of places along
a row, the same at every slice of its band. Each slice keeps, for each carrier row a question reads, a
table Q of running sums along its rows.

Figure 36 works one window through. Its footprint (A) is four runs, moved to each place of its
envelope that no other cell holds (B). At one slice, for one carrier row (C), Q[2, x + 1] counts the
places of row 2 from 0 to x that write the row. The run (1, 1, 4), moved by (+1, +1), covers places 2
to 5, and counts Q[2, 6] − Q[2, 2] = 4 − 1 = 3: two look-ups, however long the run.

```
 (A) A footprint as its runs (y, x0, x1)      (B) The footprint moved inside the envelope

         x  012345                                .ooo.     P  The predicted place
       y 0  ..##..   (0, 2, 3)                    oooox     o  A window
       y 1  .####.   (1, 1, 4)                    ooPox     x  Held by another cell: Struck
       y 2  .####.   (2, 1, 4)                    oooxx     .  Outside the envelope
       y 3  ..##..   (3, 2, 3)                    .ooo.

 (C) A moved run's count, at one slice, for one carrier row

          x       0  1  2  3  4  5  6  7
      Row 2       0  1  1  0  1  1  1  0     1: The place writes the row
                        └────────┘           Run (1, 1, 4) moved by (+1, +1)
      Q[2, ·]  0  0  1  2  2  3  4  5  5     Q[2, x + 1]: The 1s from 0 to x
                     ^           ^
                  Q[2, 2]     Q[2, 6]        Count = Q[2, 6] − Q[2, 2] = 4 − 1 = 3
```

*Figure 36.* Windows by running sums: a footprint as its runs (A), moved inside its envelope (B),
and one moved run's count read in two look-ups (C).

The search is narrowed exactly, since a window dropped by a guess would decide, unseen, where a cell
went. In three steps:
1. With the cell's cheap profile P fixed for a step, P · W sums, over the window's voxels, each voxel's
   g: P's counts on the rows that voxel writes. One running-sum table of g a slice gives every window's
   dot product at two look-ups a run, however many rows are read.
2. Where each voxel reading a metric writes exactly one of its three rows, and the question reads all
   three, ‖W‖² ≥ Σ_m N_m²/3, with N_m the window's voxels that read metric m. Three counts summing to N
   have squares summing to at least N²/3.
3. A window with 3b² · dot² < a² · ‖P‖² · Σ_m N_m² cannot reach the level a/b, and is dropped. So is
   one whose bound falls below the best cosine already found, since the look asks for the best.

Only the windows left pay for their full counts. The look searches inside the envelope, and no farther
than the plate's crowding allows. Its cost grows with cells, windows and rows read, never with voxels
times time points.

### 12.4 The Precision Ladder

The squint (§3.5) is measured, rung by rung, on a ladder of precisions. A decision drawn more finely
than its data is less correct, not more. So a categorical decision, such as whether a cell is there,
reads only as finely as it needs, and fine arithmetic runs only where the system points to something
significant: a peak, or a missed cell at another depth.

| Rung | What it holds | Who reads it | Size, and what was measured |
|---|---|---|---|
| Camera counts, 16-bit | The camera's own numbers | The camera's readings: its dark and its flicker | Never above 6,239 (under 13 bits); a voxel spans 40 to 115 steps of the camera's flicker (5.3 to 6.8 bits) |
| The 8-bit cache | Each voxel as round(scale × √count), the scale set by the time point's brightest voxel | Every stage | Half the memory of the counts; 8 bits changed a movie's run less than a random ±1-count nudge did, 6 bits lost an annotated cell, 4 bits broke the composite |
| The digit | One balanced-ternary digit a metric, against its static middle | The vectors, the cosine, recall | About 1.58 bits (§6.2) |
| Packed signs | A bundle's signs, two bit planes a bank | Storing and shipping a store | 128 bytes a bank |

The square root follows the camera's flicker, which grows as the square root of the light. The camera's
dark and flicker are read from the raw counts beside the 8-bit code, since read from the code they move
by up to 14%. Arithmetic on light decodes first and runs at full precision.

The clean-up's bundles are squinted to 8 bits by one factor, which brings the largest count to at most
127 (§9.4). One factor for the whole table moves a cosine only by its rounding. Each coarser rung is a
new version of its encoding, measured before use as the 8-bit cache was, never a silent change of type.

### 12.5 Contracts and Compiled Twins

A speed-up changes how an answer is computed, never the answer, so every compiled body answers to a
plain specification.

Every function carries a contract, data that tests read. It names the kind of work, the body's language
and the measurement that chose it, the encodings read and written, what is allocated and kept, and the
unit it can run beside others in.

Every compiled body has a **reference twin**: a plain Python or NumPy function behind the same contract,
and a test that the two agree exactly. The reference is the specification. The compiled twin (Numba, for
tight loops over small arrays) sums in the reference's order, with strict floating-point arithmetic. It
is kept only where it gives the reference's answers in both environments the system runs in.

Environments differ: two SciPy versions' Fourier transforms differ in a disc sum's last digits, by at
most 1.5 × 10⁻¹⁴ of its value. So we claim the same answer within an environment, never across two.
Whole numbers remove the question. Counts, popcounts and running sums have no order of summation to
differ in, so twins of the representation's operations are exact by construction.

### 12.6 Work in Proportion to Change

The system computes a value once, and then measures only the change, the smaller number. Cells mostly
sit, and the system mirrors them (memento mori, §2.2). Four mechanisms carry this:
- Compute once, keep, consult. A value is made once where it becomes known, and handed to every
  consumer. A **kept value** is keyed by its producer, scope, camera reading and encoding, each
  versioned, and by the state in which each slice it read last changed. It stays valid while none of
  those slices changes. Each reuse enters the kept record of findings as the fact that nothing changed
  there; each drop names its cause.
- Diffs. Between adjacent time points a place's digits change only where a reading crosses an edge of
  its static middle (§6.2). So a time point's cheap vector is updated by the places whose digits
  changed. The share that changes is measured, never assumed.
- Physics and abstention prune. Two cells cannot occupy one space, so neither the look nor the search
  for missed cells computes anything at a place a cell already holds. A lens that cannot speak at a
  depth is not computed there.
- Recall, not teaching, at run time. The memories ship as small tables of cases, each a bundle kept with
  its confirmed role, what was expected of it and how that was off, and its source (§7.1). A recall is a
  few cosines over a question's banks.

### 12.7 Organization

Being organized about what is computed, where it is handed on and where it is used is the substance of
these mechanics: a run kept so shows what every answer rested on, and who used every finding.

Functions are of three kinds, kept apart. A measurement returns a number or a field, with its scope and
provenance. A decision returns an answer or an abstention, with the evidence it rested on, as a named
word, never a bare true or false. So two conditions that mean different things never collapse into one.
An orchestration only moves values between stages. Each function is small and pure, and does one thing
a biologist could name, such as the haze of a slice.

Every categorical finding is kept as data where it is made: who made it, from which state and inputs,
whether it answered, abstained or found a disagreement, and why. Each use is kept beside it with its
consumer, so a finding never used shows itself, and the graph of what is used where can be drawn from
the record. An abstention is kept like an answer, with the reason none could be proved (§4.8).

Positions carry their provenance. A position is measured in full at an anchor, or modeled: the static
model's prediction plus, where a look settled the step, the signed shift it measured, corrected by the
error record. Neither is mistaken for the other.

The impure edge is thin: reading a movie, writing the output, drawing pictures. A picture is a pure
function from the run's values to an image array. The run asks for none and imports no drawing code, so
pictures are a layer that can be switched off. The tools that trace, time and draw this organization
check it; they do not make it.

## 13. Beyond Cells: What Generalizes

The thesis is about \<objects>, not nuclei. The preceding sections mention a nucleus only through three things that
belong to the domain: its laws, its lenses and its teaching. So what the architecture needs from a domain is not
the cell but the precondition. Here we give the recipe that sets the architecture up for another domain, work it
for the five domains the thesis names, and state the findings that would show the thesis wrong.

### 13.1 The Recipe

Nine steps, from the companion paper (Vinaik, 2026), set the architecture up for a domain that meets the
precondition. Four of them each answer one of its clauses: the laws, the lossy views, the clean signals and the
law checks. Each step uses only what earlier steps make.

1. *State the laws:* the regularities that make the picture, not regularities found in its pixels. Every later
   step reasons from them.
2. *Name one lens per term of the law.* Each lens keeps what one law makes readable and drops what the laws hold
   constant. It leaves open one quantity of its own, chosen from a few physically sane values (for cells, the
   nucleus's size at which bright centers are found, §5.2, and the radius over which the haze is read, §4.2).
3. *Read the priors as regime keys.* The priors, cheap readings of the whole field taken once, point and never
   decide alone. Their words key every case, since a quantity means one thing within a regime and another across
   regimes. They are the field's part of a case's context.
4. *Name each clean signal and the agency it is clean for.* A signal is clean for an agency when it does not
   depend on what that agency learns (a full measurement, for where a carried \<object> is). For cells, §10.1 names
   the four.
5. *Write the law checks,* in families any domain can fill. Nothing counted vanishes or appears unexplained, no two
   \<objects> occupy one space, and each \<object> is well formed. Nothing \<object>-like is left when the work is
   done, one \<object> carried two ways lands in one place, and events keep the domain's rules. Each check supports
   a judgment and never establishes one; §2.6 gives them for cells.
6. *Define the agencies by their checks.* An agency is its question, the check that judges its answers and the
   oracle that teaches it. Agencies are taught and judged apart, and truth among them is assigned by concurrence.
7. *Measure the substrate* on the domain's own data before anything is taught: whether the profiles keep the
   distinctions each question needs, which is H2's bridge, and whether the views' errors are independent. An exact
   code does not make an observation lossless.
8. *Teach each agency from its own curriculum,* the cases its own check judges, never from one pile for all.
9. *Judge each agency by its trajectory,* the course of its learning, never by one final number.

Beyond the domain's laws, lenses and teaching, the architecture carries over as it is: the loop that empties the
box, the one language, the K-lines and censors, decide or abstain, and the society. Where the domain has time, so
do the anchors, the sandwich and the Ephemeris move. The Wayfinder thesis holds in any structured domain (§4.6).
The structure removes the plain part of the problem, each \<object> with what its laws say it leaves on the
picture, as a cell goes with its halo. What remains is the same kind of problem with added context, its meaning
changed by the lawful removal (the Monty Hall move), and the same approach reads it again.

### 13.2 Five Domains by the Recipe

We work the recipe's first steps for X-rays, histology, MRI, faces and logic puzzles. Each row changes only what
belongs to its domain: its \<object>, its laws, its lenses and its teaching.

| Domain | \<Object> | Laws | Lenses | Teaching |
|---|---|---|---|---|
| Cells on a plate (this paper) | A nucleus | The optics of its light; memento mori; the plate's drift; one cell to one place | Four measures of focus, each at its own depth | An expert's calls: one cell; several, N; noise |
| X-ray | A bone; a nodule | Each ray is dimmed by all it crosses, so shadows add along the ray | Edges where the dimming changes; density; shape | A radiologist's calls |
| Histology | A nucleus; a gland | Each stain binds one kind of structure, so a color marks a kind; the section is one thin plane | One per stain; edges; shape | A pathologist's calls |
| MRI | An organ; a lesion | A tissue's brightness is set by its magnetic relaxation under the sequence; anatomy is contiguous from slice to slice | One per sequence | A radiologist's calls |
| Faces | A face and its parts | Parts in fixed relations (eyes above nose above mouth); shading follows shape; a person persists through a video | One per part; one for their relations | Calls by someone who knows the people |
| Logic puzzles | A connected shape on a grid | Shapes are contiguous; the rule acts on shapes and their roles; the background is what no role claims | Color, shape, topology and gestalt, at scales from one square to the grid | The worked input and output pairs |

Suppose the recipe is worked for the second row, a chest radiograph. Its law is attenuation: each ray is dimmed by
all it crosses, so shadows add along the ray. The instrument has already flattened depth, and no invariance
licenses that loss, as one licenses the collapse of a movie of cells. The law says what was lost: one shadow can be
two \<objects> on one ray, such as a nodule seen through a rib. Since shadows add, a rib taken out with the shadow its law says it casts leaves the nodule's own shadow behind. That residual is the same problem with added context,
and the lenses read it again.

A logic puzzle has no optics and still meets the precondition: a discrete state, contiguous \<objects>, and worked
pairs as a clean check. In every row but the last, the expert's part has the form it has for cells: calls in plain
words on the hardest candidates, written as ternary digits. The expert's part is the same few hours and few dozen examples there.

### 13.3 What Would Show the Thesis Wrong

Each hypothesis rests on a bridge that a domain can fail to supply. Six findings, each measured on the domain,
would falsify the thesis there.

1. *Lenses that cannot resolve most of the problem.* If step 2's lenses, one per term of the domain's laws, do not
   resolve most of the problem in concurrence and over rounds, H1 fails there. The structure then leaves the whole
   problem, not a typed residue.
2. *No clean signal for an agency.* Every case keeps its source, what confirmed it. Without a clean signal, an
   agency's cases have no source outside it, and its memory confirms itself. H4's bridge, that an independent
   signal establishes, then fails.
3. *A substrate that loses what a question needs.* If the profiles of \<objects> an expert calls apart do not
   differ, recall has nothing to recall by, and H2 fails. For cells, objects called one cell and objects called
   several must show apart in their profiles.
4. *Similar situations that do not lead to similar results.* Recall by precedent rests on Winston's precondition,
   the bridge of H3 (§7.4). Where resemblance does not predict the interpretation that holds, a K-line brings back
   the wrong one, and H3 fails.
5. *Learning that does not settle.* Learning in the classical sense pre-empts a mistake when its context recurs.
   If an agency's rules keep changing, or its wrong answers fall only as its abstentions swallow the gain, the
   memory is storing instances rather than forming rules (§10.4). Where more structure makes the learning settle,
   the structure was incomplete; where none does, H4 fails in that domain.
6. *Cost that does not fall.* As the agencies learn, full measurements should grow fewer and looks cheaper, toward
   no full re-measure beyond the anchors. If teaching made the system right only by making it expensive, the claim
   that understanding is cheap would fail.

### 13.4 Where Parts of the Design Began

Parts of the design began in earlier work by one of us (Vinaik), on abstract-reasoning puzzles drawn as grids and
on encoding DNA. From the puzzles came a background found by exclusion, which returns here as reading by exclusion
and in the censors, and a structural profile written into banks, which H2 keeps. From the work on DNA came the
carrier, the exact, whole-numbered object every vector is written in. DNA's repair is also why every place's
vector carries every scale it belongs to (§6.1).

## 14. Conclusion

We asked what a computer must know before it can see, and answered: what an \<object> is. An \<object>
is the kind of thing a general computer vision must recapitulate, a thing with physical presence
that is contiguous and closed, persists through time, moves by physics and signals by laws the
instrument obeys. A computer that holds that concept can do what Minsky and Papert meant by vision:
build and reason with descriptions of the things in a picture, their relations and what they can do.
We argued the claim as four hypotheses and showed their elements working on four-dimensional movies
of cells on a plate.

Taken together, the hypotheses say that understanding a picture of physical things is mostly
reasoning and a little memory, and that both are cheap for the same reason. H1 says the reasoning
does most of the work. The laws license deliberate losses: the data is read coarsely along every
dimension in which an \<object> barely changes. On the running instance, a movie collapses into flat
stills at independent depths and into three time points resolved in full. They license removals:
each \<object> found leaves the data with the signal it spreads, and what remains is the same problem
with added context, read again until nothing \<object>-shaped is left. And they license borders,
drawn from the data's topology, within which one \<object> holds one space. What the structure leaves
is a typed residue. H2 says that everything the reasoning measures can be written in one exact
language, so that any two readings can be compared, any difference has a name, and every place
carries every scale it belongs to. H3 says that the bundles this language needs are exactly the
substrate of K-lines and censors. The bundle of a case an expert confirmed is the cue of a K-line,
and recall brings back the interpretation the case confirmed and the procedure it routes to. A few
dozen such cases make a memory that bends the borders the structure draws: every confirmed \<object>
is one more peak the noise line avoids. H4 says that the residue, the questions the structure leaves
open, is taken up by a society of agencies, each taught by its own clean signal. Each decides or
abstains, and truth among them is assigned by concurrence and refused on disagreement; in time,
identity comes first and position is then cheap.

The four close a loop. The structure sees, and the language writes what it sees. The memory
remembers what an expert confirmed and helps the structure see better. The society organizes what
remains, including time. Each hypothesis rests on the one before, and each rests on a bridge stated
rather than assumed. The laws license exactly these losses and removals; the profiles keep the
distinctions a question needs; similar situations generally lead to similar results; and an
independent signal, never a law check alone, establishes a judgment. What is learned stays small and
inspectable: a departure from what was expected, kept with how it was off and in what context. So
every answer the system gives can be traced to a law, a reading or a case an expert confirmed, and
where no answer can be proved, the system abstains and keeps the question open. Answers given only
under proof, and principled abstention where there is none, are among the strengths of a law-based
design.

Nothing in the architecture names a nucleus except its laws, its lenses and its teaching. The loop
that empties the box, the one language, the K-lines and censors, the society, and, where a domain
has time, the anchors, the sandwich and the Ephemeris move are written without a cell. What the
architecture needs is the precondition (§1.3), and §13 works the recipe for X-rays, histology, MRI,
faces and logic puzzles drawn as grids.

The thesis can be shown wrong: §13.3 names six findings that would show it, each a measurement on a
domain. The design keeps what each measurement needs: every case keeps its source, every agency is
judged by the course of its learning, and every finding is kept as data.

Under all of it lies one idea. A problem's structure carries information from outside any local
question into it, and the design hands its computation to that structure. Each instance §1.5 lists,
from the signal that goes out with its \<object> to the censors, is that idea at one step. The local
question is answered cheaply, and a local error is corrected by what surrounds it.

The spirit is economy, the domain's own. Physical things change only as their laws let them, and
living things spend energy only where they must: cells sit, jiggle and divide when the time is
right. The system spends computation the same way. It gets each \<object>'s state once and measures
the change, the smaller number. It resolves a moment in full only at its anchors, or where a bound
says it must, and it hands to the laws whatever they already answer. It does the least computation
that answers, as life does the least that lives, and it is cheaper and cleaner for the same reason.

What an \<object> is, then, is not a label attached to pixels. It is a region the structure can
enclose, a light the optics explain, a profile the language writes, a case an expert confirmed, and
a track the laws carry through time. People reason on objects. A computer that knows what an
\<object> is reasons on \<objects>, and that, in the sense Minsky and Papert gave the words, is
computer vision.

## References

- Clowes, M. B. (1971). On seeing things. *Artificial Intelligence*, 2(1), 79–116.
  doi:10.1016/0004-3702(71)90005-1.
- Good, I. J. (1950). *Probability and the Weighing of Evidence.* London: Charles Griffin.
- Gotoh, O. (1982). An improved algorithm for matching biological sequences. *Journal of Molecular
  Biology*, 162(3), 705–708. doi:10.1016/0022-2836(82)90398-9.
- Groen, F. C. A., Young, I. T., and Ligthart, G. (1985). A comparison of different focus functions
  for use in autofocus algorithms. *Cytometry*, 6(2), 81–91. doi:10.1002/cyto.990060202.
- Guzman, A. (1968). *Computer Recognition of Three-Dimensional Objects in a Visual Scene.*
  Technical Report AI-TR-228, MIT Artificial Intelligence Laboratory, December 1968 (cataloged
  under Guzman-Arenas, Adolfo).
- Huffman, D. A. (1971). Impossible objects as nonsense sentences. In B. Meltzer and D. Michie
  (Eds.), *Machine Intelligence 6* (pp. 295–323). Edinburgh University Press.
- Kanerva, P. (2009). Hyperdimensional computing: An introduction to computing in distributed
  representation with high-dimensional random vectors. *Cognitive Computation*, 1(2), 139–159.
  doi:10.1007/s12559-009-9009-8.
- Kunkel, T. A., and Erie, D. A. (2005). DNA mismatch repair. *Annual Review of Biochemistry*, 74,
  681–710. doi:10.1146/annurev.biochem.74.082803.133243.
- Mandelbrot, B. (1967). How long is the coast of Britain? Statistical self-similarity and
  fractional dimension. *Science*, 156(3775), 636–638. doi:10.1126/science.156.3775.636.
- Marr, D., and Hildreth, E. (1980). Theory of edge detection. *Proceedings of the Royal Society of
  London, Series B*, 207(1167), 187–217. doi:10.1098/rspb.1980.0020.
- Minsky, M. (1979). *K-Lines: A Theory of Memory.* MIT AI Memo 516, June 1979; revised in
  *Cognitive Science*, 4(2), 117–133, 1980, doi:10.1207/s15516709cog0402_1.
- Minsky, M. (1986). *The Society of Mind.* Simon & Schuster.
- Minsky, M. (1994). Negative expertise. *International Journal of Expert Systems*, 7(1), 13–19.
- Minsky, M., and Papert, S. (1971). *Progress Report on Artificial Intelligence.* MIT Artificial
  Intelligence Memo 252, December 11, 1971 (cataloged by MIT as *Artificial Intelligence Progress
  Report*, January 1, 1972).
- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on
  Systems, Man, and Cybernetics*, 9(1), 62–66. doi:10.1109/TSMC.1979.4310076.
- Papert, S. A. (1966). *The Summer Vision Project.* MIT Project MAC, Artificial Intelligence Group,
  Vision Memo No. 100 (AI Memo 100), July 7, 1966.
- Roberts, L. G. (1963). *Machine Perception of Three-Dimensional Solids.* Ph.D. thesis, Department
  of Electrical Engineering, Massachusetts Institute of Technology.
- Selvin, S. (1975). A problem in probability [letter]. *The American Statistician*, 29(1), 67.
- Sun, Y., Duthaler, S., and Nelson, B. J. (2004). Autofocusing in computer microscopy: Selecting the
  optimal focus algorithm. *Microscopy Research and Technique*, 65(3), 139–149.
  doi:10.1002/jemt.20118.
- Vinaik, R. (2026). *Structured Symbolic AI: How a Domain Thought Random Becomes a Solvable
  System.* Companion paper, manuscript.
- Waltz, D. L. (1972). *Generating Semantic Descriptions from Drawings of Scenes with Shadows.* Ph.D.
  thesis, MIT, September 1972; issued as MIT AI-TR-271, November 1972.
- Waudby-Smith, I., and Ramdas, A. (2024). Estimating means of bounded random variables by betting
  (with discussion). *Journal of the Royal Statistical Society Series B: Statistical Methodology*,
  86(1), 1–27. doi:10.1093/jrsssb/qkad009.
- Winston, P. H. (1970). *Learning Structural Descriptions from Examples.* Ph.D. thesis,
  Massachusetts Institute of Technology, January 1970; issued as MIT Project MAC TR-76 and MIT
  AI-TR-231, September 1970.
- Winston, P. H. (1980). *Learning and Reasoning by Analogy: The Details.* MIT AI Memo 520, April
  1979, revised June 1979, January 1980 and May 1980; a shorter form appeared as "Learning and
  reasoning by analogy", *Communications of the ACM*, 23(12), 689–703, 1980.
- Winston, P. H. (2010). *6.034 Artificial Intelligence*, Fall 2010. MIT OpenCourseWare lecture
  transcripts: Lecture 7, "Constraints: Interpreting Line Drawings"; Lecture 8, "Constraints:
  Search, Domain Reduction".
