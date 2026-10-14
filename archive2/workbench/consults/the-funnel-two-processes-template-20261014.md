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

{WORDS}

## The rules under check (the design's section 9, verbatim)

{SECTION}
