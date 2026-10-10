Do not use any tool, run any command or read any file. Answer from this text alone.

Before you read: the last time you were consulted on this project, you graded a design and proposed changes to it
as if you could judge what works. You cannot. Nothing is built, there is no evidence of anything, and the design
is the founder's. In his words: "*I* am the authority on what works or doesn't. ... You do not have the authority
to change the design *I* built based on a random guess, when you don't know the intent". This time you are a
common-sense check on one reader's understanding of what he said. Say where it misses or distorts his words. Do
not add a design of your own. (The project is deterministic, classical-AI computer vision of knee MRI, with no
machine learning.)

The founder's words, verbatim:

"""
When I say that no single lens is allowed to have a warrant, complete unilateral authority on a decision, I am saying something very explicitly grounded in information theory. This is a thesis based on the work I did in the "what is an <object>" thesis on computer vision. Specifically, lenses that are intentionally lossy, that do not encode a specific 1:1 relationship to a specific element of "truth", do not have authority to warrant a decision unilaterally. A lens is an instrument, an artifact of observation. It does not say "this is the purpose of <X>". It simply measures, says things like "the intensity is <X>" or "the variance of the signal in this location is increasing with a directional vector of <x,y>". The interpretation is a construction on top of them. If the *meaning* of what they observe is definable, then it is encoded as such. So, the answer to question 1 is dependent on what you define as "direction", "exclusion", and "lenses". A measurement is different from a statement of truth. Properly-designed lenses are never wrong, by definition. They only measure something, a specific and objective fact of the problem space. The reason why this is described as "computer vision" is because we assign an interpretation of what these signals mean. The "<object>" thesis really goes into depth about this with the worked example of cell microscopy

On "the halo", again, this is where the information-theoretic concept here is really important to understand. A halo can be both. Are you trying to see if there's an active fracture? Well, fractures have concomitant edema when they're relatively fresh, no? So in that case, it's actually *part* of what assigns meaning to other lenses that see something that looks kind of like a fracture but can't fully warrant. But when it comes to the question of "what are the specific <x,y> coordinates of the line-drawing process that traces the exact fracture, then edema is noise to remove. The point here isn't to find some clean metric that hands you the perfect and complete answer. This is the core part of why and how this is a deterministic and classical AI computer vision approach. Meaning is derived from structure, not computed from some magical metric that solves everything.

This should also address "independence classes". The answer to "A ≇ B", "B ≇ C", and "A ≠ C" is "yes". That's not a contradiction, it's a finding. The epistemology of deterministic approaches to machine intelligence is principled abstention--you know what you know, you know what you don't know, and those are both complete and correct assertions of the process of reasoning

I think this is rather enough to get started. Think about it, think through the theory this is based on and how it informs your understanding of the whole project, and take it to codex too to work it out. Then, we see what we need to change about the project design to properly adhere to this load-bearing principle
"""

One reader's understanding of those words:

1. **A lens is an instrument.** It measures one objective fact of the problem space, lossily and on purpose: an
   intensity, a variance and the direction it grows in, a volume, the length of a run. It says nothing about what
   the fact means. Because it claims only the measurement, a well-built lens is never wrong.
2. **So no lens warrants a decision alone.** A lossy view bears no one-to-one relation to any element of the truth.
   In information terms, one reading carries too little about the truth to settle it, however reliable the reading
   is as a measurement. "The intensity here is high" is a fact. "There is a lesion here" is a claim the reading
   cannot make on its own.
3. **Meaning is built on top of the measurements, in two ways.**
   - *Where a meaning is definable,* it is written down explicitly, as a law: a law of the instrument's physics or
     of anatomy that says what an observation means. Such an encoded law is part of the structure, not a power of
     the lens.
   - *Otherwise, meaning comes from structure.* It comes from the question being asked, from what has already been
     explained and removed, from how independent readings agree or disagree, and from how a profile compares with
     confirmed examples. No single metric computes it.
4. **One signal can have different roles for different questions.** Take edema near a fracture. For "is there an
   active fracture?", the edema is evidence that gives meaning to a line-like reading that could not warrant
   anything alone. For "where exactly does the line run?", the same edema is noise to remove first. The role
   belongs to the question and the structure, not to the signal.
5. **Abstention is a correct statement.** Knowing what is known and knowing what is not known are both complete
   and correct results of reasoning. Take "A cannot be told apart from B, B cannot be told apart from C, but A and C
   are separate". That is recorded as found, not forced into a tidy grouping. Where the structure cannot establish
   an answer, the system abstains, and that is a result, not a failure.
6. **What this asks of the knee's design, as I read it.**
   - Every lens is specified as a measurement only: its value, its digit, its silences and their causes, and where
     it came from. Nothing in a lens says "for" or "against".
   - Words like "direction" and "exclusion" in the design must each be read as one of two things. One is a measured
     fact, such as which way a gradient points. The other is an explicitly encoded law of meaning, such as "this
     tissue signature cannot coexist with that finding". Neither is the lens's own claim.
   - Every place where a single reading alone settles a decision is to be found and checked. Either it rests on a
     meaning that is definable and encoded as a law, or the decision must come from structure, or the system
     abstains.
   - A pairwise finding about which acquisitions fail together is kept as found, with no grouping imposed on it.
   - A rule that lets one signal play only one role, such as "edema is never a halo", is wrong under the principle.

The question: is this understanding what he is saying? What important or obvious point does it miss or distort?
Where does it add something he did not say? Quote his words for each point you make. Keep it short.
