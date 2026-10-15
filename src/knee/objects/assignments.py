"""Name the objects that are plain in the interiors' pictures, one at a time.

Each is an «<object>» (Rohan, 2026-10-14): a set of descriptions of how it appears in these scans,
read off the interiors' own lenses, each one check with the code it abstains with, and the
categories of the twelve it relates to (docs/OBJECTS_AND_CONDITIONS.md §6):

- AIR: the low signal outside the leg. Measured on the proof study, 2026-10-14: the air fields are
  2.5 to 5 cm thick, and the strips where the picture fades into its black margin are a few
  millimetres; those strips are not air. Its descriptions, each one check with its code:
  1. there is a leg on the slice: every territory, its holes filled (abstain_no_leg);
  2. it is the measured low signal outside the leg and its black margin, where it forms a field at
     least `AIR_FIELD_MM` thick (`fields`) (abstain_no_field_outside_the_leg).
  Where the lens draws the air into its territories, as on the proof's T1 coronal, none lies
  outside the leg; there it is laid on from the other sequence's slice of the same place
  (`with_partner`), which names it (laid_from_its_partner).
  It relates to none of the twelve categories: it is the field the leg lies in.
- SKIN: the leg's edge against the air. Its descriptions, each one check with its code:
  1. there is air on the slice (abstain_no_air);
  2. it is the leg's places that touch the air.
  Where the slice names no air of its own, the skin too is laid on from the other sequence's slice
  of the same place (laid_from_its_partner).
  It relates to none of the twelve categories. Seen also on the proof: laid onto the T1 coronal,
  the skin lies on the dark rim between the air and the bright fat, on the rim's outer side, and a
  few specks of the laid air lie apart from the rest.
- FEMUR and TIBIA: each is its own large territory, and they hold the strongest interior peaks, one
  above the other along the leg (Rohan, 2026-10-13, on the proof figure: «Good»). Their
  descriptions, each one check with its code (`pair_code`):
  1. the leg runs in the plane, more along it than across (abstain_leg_runs_through_the_plane);
  2. the slice holds at least two territories (abstain_fewer_than_two_territories);
  3. they are the territory with the deepest peak and the deepest one above or below it along the
     leg; the upper is the femur and the lower the tibia
     (abstain_nothing_above_or_below_the_deepest).
  Read with the other sequence's slice of the same place, each is kept where both name it or the
  partner's picture does not reach (agreed_with_its_partner), laid on where only the partner names
  it (laid_from_its_partner), and dropped where they share no place
  (abstain_the_two_slices_disagree). The femur relates to Medial, Lateral and PF OA, Contusion,
  Fracture, and the ACL and MCL by their attachments; the tibia to Medial and Lateral OA,
  Contusion, Fracture, the ACL and MCL by their attachments, and both meniscus tears, as the
  plateau beneath them.
- BONE MARROW: the inside of each bone named here. A bone's territory is its inside, within its
  dark shell, so the marrow has no check of its own: it is named where its bone is. It relates to
  Contusion, Fracture and the three OA categories, by the changes beneath the joint surfaces.
- ARTICULAR CARTILAGE: the layer on each bone's joint surface, 2 to 3 mm thick where the femur's
  condyles meet the tibia's plateau. Seen on the proof's fat-suppressed coronal, 2026-10-14: down
  each column across the joint, the femur's marrow, its dark shell, a bright layer (x2.4 to x3.5
  of the marrow's light), the dark joint line, the tibia's bright layer, its shell, its marrow. Its
  descriptions, each one check with its code (`cartilage_code`):
  1. side to side lies in its slice's plane, as on a coronal slice; the middle sagittal slice,
     which side to side runs through, passes through the notch, where no joint surfaces meet
     (abstain_side_to_side_runs_through_the_plane);
  2. fat is suppressed: without it the layer is not brighter than marrow, and there it is laid on
     from the fat-suppressed slice of the same place (`with_partner`)
     (abstain_not_brighter_than_marrow_without_fat_suppression);
  3. the slice names the joint (abstain_no_joint);
  4. it is the places in the joint brighter than the bones' marrow by `CARTILAGE_BRIGHTER`, within
     `CARTILAGE_MM` of a bone, named for the nearer bone, femoral or tibial (`cartilage_on`)
     (abstain_nothing_bright_against_the_bones).
  It relates to Medial, Lateral and PF OA. Seen also on the proof: the bright fluid down the
  femur's outer side, and the lining of the notch's roof, lie in the joint within that reach and
  are named with it; the joint's fluid, named after it, is the white beyond its reach.
- JOINT: what lies between the femur and the tibia along the leg. Its descriptions, each one check
  with its code:
  1. the slice names the femur and the tibia (their codes, above);
  2. it is the places between them on each line along the leg, outside the black margin
     (`between_along_the_leg`) (abstain_nothing_between).
  It relates to the three OA categories, by its narrowing, and to Effusion and Synovitis, whose
  fluid and lining it holds.
- PATELLA: the bone in front of the femur's lower end, on a sagittal slice. Its marrow is the
  femur's tissue, so it is about as bright as the femur, and it has its own peak there. Seen on the
  proof's two middle sagittals, 2026-10-14 (the patella is plain to the eye in both): with fat
  suppression the patella is a solid oval as dark as the femur, and the fat pad below it is half
  again to two and a half times brighter, so its light parts them; without fat suppression the fat
  pad is as bright as marrow, and two territories meet across the patella's lower part, so there
  light and territory cannot part them. Its descriptions, each one check with its code
  (`patella_code`):
  1. front to back lies in its slice's plane, as on a sagittal slice
     (abstain_front_to_back_runs_through_the_plane);
  2. the slice names the femur (abstain_no_femur);
  3. fat is suppressed: without it the fat pad is as bright as marrow, and there it is laid on from
     the fat-suppressed slice of the same place, only where it holds this slice's own peak in
     front of the femur (abstain_fat_as_bright_as_marrow; abstain_the_two_slices_disagree);
  4. a peak lies in front of the femur, no higher than `PATELLA_ABOVE_MM` above its lowest place;
     the deepest such (`patella_peak`) (abstain_no_peak_in_front_of_the_femur);
  5. it is the places in that peak's territory within `LIKE_THE_FEMUR` of the femur's light, the
     piece holding most of the peak's own disc, its holes filled (`patella_piece`)
     (abstain_nothing_like_the_femur_at_its_peak).
  It relates to PF OA, Contusion and Fracture.
- PCL: the posterior cruciate ligament, «thick, uniformly low-signal and curvilinear», from the
  femur's notch to the back of the tibia (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's
  middle T2 sagittal, 2026-10-14: a thick dark band behind the femur's condyle curving down to the
  back of the tibia, x0.05 to x0.25 of the marrow's light; the low-signal lens marks only dots in
  it, the signal itself shows it whole. A ligament joins two bones. Its descriptions, each one
  check with its code (`pcl_code`):
  1. front to back lies in its slice's plane, as on a sagittal slice
     (abstain_front_to_back_runs_through_the_plane);
  2. fat is not suppressed: with it the marrow is as dark as a ligament, and there it is laid on
     from the other slice of the same place
     (abstain_marrow_as_dark_as_a_ligament_with_fat_suppression);
  3. the slice names the femur and the tibia (abstain_no_femur_and_tibia);
  4. it is the places whose light over `LIGAMENT_SMOOTH_MM` (uniformly dark, not speckled) is under
     `LIGAMENT_DARKER` of the femur's marrow, outside the black margin (a stored zero inside the
     leg is the darkest tissue there, not the margin), at least `LIGAMENT_THICK_MM` thick (the
     bones' thin shells drop out): the slice's dark bands (`dark_bands`), of which it is the
     largest reaching within `SHELL_MM` of both the femur and the tibia (`band_joining`)
     (abstain_no_dark_band_joins_the_bones).
  It relates to none of the twelve categories directly: it is the ACL's neighbour in the notch.
  Seen also on the proof: on the middle slice it takes in the ACL's lower fibres, which cross in
  front of it in the same dark, and its last stretch down the back of the tibia stays with the
  dark tissue behind the tibia; where the femur's shell, stored as zero, touches it at the
  condyle's back, it takes in a thin strip of the shell.
- ACL: the anterior cruciate ligament, inside the notch from the tibia's front-middle up and back
  to the inner wall of the femur's outer condyle; «less well defined than the PCL», «its bundles
  outlined by surrounding high-intensity structures», and «going lateral to medial, the ACL comes
  before the PCL» (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's two sagittals, 2026-10-14:
  on the middle slice the ACL's lower fibres cross in front of the PCL in the same dark; on the next
  slice toward the knee's outer side (slice 19), the T2 shows it as a dark band from the femur's
  back down and forward to the tibia's front-middle, striated toward the tibia, and the
  fat-suppressed slice shows it as a grey, streaked body walled off by the bright fluid round it,
  which the lens draws as a region of its own with its own peak. So it is named on its own slice by
  these descriptions, each one check with its code (`acl_code`):
  1. front to back lies in its slice's plane, as on a sagittal slice
     (abstain_front_to_back_runs_through_the_plane);
  2. it lies on the knee's outer side of the middle slice, which on the proof holds the PCL: its
     slice is the middle slice's neighbour on the side the header names as outer (`outer_step`),
     chosen by place and not read off the squint (abstain_header_names_no_knee);
  3. it lies between the femur and the tibia, carried to its slice from the middle one by place,
     each the regions most of whose places were that bone there, since the lens may split a bone
     in two there (`carried_bone`; anatomy is contiguous from slice to slice; the fibula's rule
     carries the one region holding most of the tibia) (abstain_no_femur_and_tibia_to_carry);
  4. the fluid round it walls it off, which it does only with fat suppression; without it, the fat
     and the ligament fall in one region, and the ACL is laid on from the fat-suppressed slice of the
     same place (abstain_not_walled_off_without_fat_suppression);
  5. its body is the region the lens draws whose peak lies in the joint between those bones, along
     the leg; the deepest such (`acl_on_slice`) (abstain_no_region_in_the_joint).
  It relates to the ACL category, «anterior cruciate ligament injury». Seen also on the proof: it
  takes in the fluid round it and a patch down toward the tibia, and leaves its top end at the
  femur.
- MCL: the medial collateral ligament, «a uniformly low-signal line» on the medial side of the
  joint, «from epicondyle to tibia», «joined to the medial meniscus», seen on «coronal images
  first» (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's fat-suppressed coronal, 2026-10-14:
  outside the medial meniscus a dark band crosses the joint line from beside the femur to beside
  the tibia, and the low-signal lens marks it; its stretch down the tibia's inner side is a second
  band 2 to 3 mm below it, and up the femur only dots. On the T1 coronal the lens does not mark it
  and the femur's and tibia's regions take its place, so there it is laid on from the
  fat-suppressed slice of the same place (`with_partner`). It is named by these descriptions, each
  one check with its code (`mcl_code`):
  1. side to side lies in its slice's plane, as on a coronal slice
     (abstain_side_to_side_runs_through_the_plane);
  2. it lies on the inner side of the joint, the side of the medial meniscus, which the header's
     word for which knee sides (abstain_no_medial_meniscus);
  3. it is low signal the lens marks, outside every part already named, on that side of the
     joint's middle, joining the femur and the tibia: the largest such piece reaching within
     `SHELL_MM` of both (`ligament_on_the_inner_side`)
     (abstain_no_low_signal_joins_the_bones_on_the_inner_side).
  It relates to the MCL category, «medial collateral ligament injury». Seen also on the proof: it
  is named only where it crosses the joint line, about 12 mm of it; its stretches down the tibia
  and up the femur are not reached; and the femur's region, which takes in the fluid of the inner
  recess, lies between it and the meniscus, so the meniscus marks its side and is not reached.
- LCL: the lateral, or fibular, collateral ligament, «a thin cord about 5 cm long» from the femur's
  outer condyle to the fibula's head, «not attached to the lateral meniscus»
  (docs/OBJECTS_AND_CONDITIONS.md). It attaches on the outer side of the fibula's head,
  `LCL_BEHIND_MM` behind its front edge, and on the femur just above and behind the lateral
  epicondyle (LaPrade et al. 2003). Seen on the proof's coronals, 2026-10-15: on the slice through
  that place, the T1 shows a grey band on the knee's outer side between the bright fat under the
  skin and the bones, from beside the femur's outer condyle down to the fibula's head, the dark
  cord in it, and the lens draws the band as a region of its own; with fat suppression the fat
  under the skin is as grey as the band, and the lens draws the two as one strip, so there it is
  laid on from the T1 slice of the same place. It is named on its own slice by these descriptions,
  each one check with its code (`lcl_code`):
  1. side to side lies in its slice's plane, as on a coronal slice
     (abstain_side_to_side_runs_through_the_plane);
  2. its lower end is on the fibula, the one its own rule names on a main slice where front to back
     lies in the plane, so its front edge can be read, carried here by place, since it is one leg
     (abstain_no_fibula);
  3. the middle slice names the femur, carried to its slice as the regions most of whose places
     were the femur (`carried_bone`), and the tibia, whose middle marks the knee's middle
     (abstain_no_femur_and_tibia_to_carry);
  4. its slice is the one through the place where it attaches on the fibula (`lcl_attachment`,
     `slice_through`) (abstain_attachment_off_the_slices);
  5. fat is not suppressed: with it the band and the fat under the skin fall in one region, and
     the LCL is laid on (abstain_not_parted_from_the_fat_with_fat_suppression);
  6. the fibula's places on that slice (`places_on_slice`) lie in a region the lens draws
     (`region_holding`) (abstain_no_fibula_on_the_slice);
  7. its body is the region the lens draws, neither the femur's nor the fibula's, whose middle lies
     on the fibula's side of the tibia's middle, the knee's outer side, and that reaches within
     `SHELL_MM` of both; the largest such (`lcl_on_slice`)
     (abstain_no_region_joins_the_femur_and_the_fibula).
  It relates to none of the twelve categories directly: it is the MCL's counterpart on the outer
  side. Seen also on the proof: the band is wider than the cord, so it takes in the tissue round
  it and, at its top, the popliteus tendon at the condyle's notch, and it leaves the cord's upper
  stretch beside the condyle to the region above. On a T1 the fibula's head may share a region
  with the tibia, so the fibula's region is a target only; the fibula is drawn on the slice as its
  own places, carried from its main slice. The source's other reading of the attachment, 38% of
  the head's width behind its front, gives the proof's next slice back (22), where the T1's lens
  draws the band in with the femur's region; the rule keeps the abstract's 8.2 mm, chosen before
  either slice was looked at.
- JOINT FLUID: the fluid of the joint's cavity and its recesses, «low on T1W, high on T2W, very
  high on fat-suppressed T2W», told apart by «fluid signal in the joint's own recesses»
  (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's fat-suppressed middle slices, 2026-10-15:
  on the coronal the white down the outer gutter beside the femur's condyle and in the notch, on
  the sagittal the white above the patella and along the joint's front, x4 to x8 of the bones'
  marrow light; the popliteal vessels and the vessels under the skin are as white, but lie away
  from the joint and the bones. Its descriptions, each one check with its code (`fluid_code`):
  1. the sequence is fat-suppressed and fluid-sensitive (the series' own tags), where fluid is
     white; on any other it is laid on from the partner slice of the same place (`with_partner`)
     (abstain_fluid_not_bright_on_this_sequence);
  2. the slice names the femur and the tibia (abstain_no_femur_and_tibia);
  3. it is the places in the leg, outside every part named but the joint, at least
     `FLUID_BRIGHTER` times as bright as the bones' marrow, the pieces of them that touch the joint
     or lie within `SHELL_MM` of the femur, the tibia or the patella (`fluid_in_the_recesses`)
     (abstain_no_bright_fluid_in_the_recesses).
  It relates to Effusion, whose excess it is, and to Synovitis, whose lining it lies against. Seen
  also on the proof: fluid is sought only among the places no other part holds when the slice is
  first read, so the white the femur's and tibia's regions take in at the recesses, such as the
  white at the outer joint line on the coronal, is not reached; it is never sought inside a bone's
  region, since white inside a bone with fat suppression is a bruise (Contusion), not fluid. The
  cartilage, named first, takes in the white in the joint within its reach of a bone, so at the foot
  of the outer gutter the white is named cartilage and the fluid is the white above it. The axial
  names no femur, so it names no fluid.
- SYNOVIUM, located at the anterior recess's fat-facing surface, and ANTERIOR SYNOVIAL RECESS:
  the lining and its cavity are different outputs, separate from the joint fluid. Descriptions:
  1. the slice is sagittal (abstain_not_a_sagittal_slice);
  2. fluid is bright on a fat-suppressed, fluid-sensitive sequence
     (abstain_fluid_not_bright_on_this_sequence);
  3. the patella and femur are named (abstain_no_patella; abstain_no_femur);
  4. the recess is the largest connected body of the existing white-fluid measurement intersecting
     the place behind the patella, in front of the femur and above the patella's lower end,
     outside the named solid structures (abstain_no_fluid_in_the_anterior_recess);
  5. its anterior boundary, facing the fat pads, locates the synovial lining. It is sampled on
     the fluid side of that interface; this is not membrane thickness or a claim to its full extent.
  The cavity and surface are retained as separate masks, since a lining surface and its fluid
  cannot be faithfully expressed by competing for one integer label. On the proof's sagittal
  the large bright pocket behind the patella is resolved. The definition uses anatomical order
  and the existing fluid reading, with no new numerical cutoff. The cavity relates to Effusion,
  the lining to Synovitis. Both are laid onto the twin by the existing physical-place match.
- HOFFA'S FAT PAD: the infrapatellar fat pad, which «lies just behind the patellar tendon and
  follows subcutaneous fat on all sequences» (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's
  middle sagittals, 2026-10-15: with fat suppression it is the grey, striated triangle below the
  patella, behind the patellar tendon and in front of the joint, x1.5 to x2.5 of the femur's light,
  and the lens draws it in one territory with the patella, which the patella's own light has
  already carved out; without fat suppression it is as bright as the patella's marrow, and the
  lens draws the two across the patella's lower part. Its descriptions, each one check with its
  code (`fat_pad_code`):
  1. front to back lies in its slice's plane, as on a sagittal slice
     (abstain_front_to_back_runs_through_the_plane);
  2. fat is suppressed: without it the fat pad is as bright as the patella's marrow, and it is laid
     on from the fat-suppressed slice of the same place (`with_partner`), where the two are parted
     (abstain_fat_as_bright_as_marrow);
  3. the slice names the patella by its own light (abstain_no_patella);
  4. it is the rest of the patella's territory below the patella's lowest place along the leg,
     outside every part named (`rest_of_the_patellas_territory`)
     (abstain_nothing_below_the_patella).
  It relates to none of the twelve categories directly. Seen also on the proof: its back part,
  tucked between the femur's condyle and the tibia, is named joint, and its top edge is cut level
  with the patella's lowest place; the patellar tendon, named after it, takes back the band's
  places it held at the tendon's back edge.
- SUPRAPATELLAR FAT: the two fat pads above the patella, the quadriceps (anterior suprapatellar)
  fat pad and the prefemoral (posterior suprapatellar) fat pad, which lie «on either side of the
  suprapatellar recess» (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's middle sagittals,
  2026-10-15: above the patella, behind the quadriceps tendon's dark band and in front of the
  femur, the lens draws the fat in one territory with the patella, as it draws Hoffa's below it.
  The recess between the two pads is collapsed, as it normally is («Normally it holds only a small
  amount of fluid»): with fat suppression a film of faint white lines, under the fluid's level,
  and without it a faint dark curve; no lens draws it as a border. So the two pads are named
  together, as the fat above the patella, and not parted. Its descriptions, each one check with its
  code (`fat_pad_code`, above the patella):
  1. front to back lies in its slice's plane, as on a sagittal slice
     (abstain_front_to_back_runs_through_the_plane);
  2. fat is suppressed: without it the fat is as bright as the patella's marrow, and it is laid on
     from the fat-suppressed slice of the same place (`with_partner`)
     (abstain_fat_as_bright_as_marrow);
  3. the slice names the patella by its own light (abstain_no_patella);
  4. it is the rest of the patella's territory above the patella's highest place along the leg,
     outside every part named (`rest_of_the_patellas_territory`)
     (abstain_nothing_above_the_patella).
  It relates to none of the twelve categories directly: the recess between its two pads is where
  the joint's fluid gathers in Effusion. Seen also on the proof: the two pads are one name, with
  the recess's film inside it; the picture's top edge cuts it; and the quadriceps tendon, named
  after it, takes back the band's places it held at the tendon's back edge. Parting the two pads
  is owed.
- PATELLAR TENDON and QUADRICEPS TENDON: the extensor mechanism's two tendons, «The quadriceps
  tendon, patella and patellar tendon; both tendons uniformly low and best seen on midsagittal
  images»; «the patellar ligament runs from its apex to the tibial tuberosity», and the quadriceps
  tendon is «laminated, its layers separated by fat» (docs/OBJECTS_AND_CONDITIONS.md). Seen on the
  proof's middle sagittals, 2026-10-15: on the T2, one black band, light 0 to 25 against the
  fat's 280 to 600 on either side, comes down the front of the knee from the picture's top edge
  to the patella's upper pole, runs along the patella's front, and goes from its lower pole down
  to the front of the tibia's top, about 3.4 mm thick below the patella; its darkest places are
  stored as zero. With fat suppression the same band is about 2.5 mm thick between fat suppressed
  to grey, so over `LIGAMENT_SMOOTH_MM` it is not uniformly dark, and the lens draws it as the
  border between two of its regions. On the T2 it is one of the dark bands the PCL is read from
  (`dark_bands`). It is named on the T2 once the patella is laid on from the fat-suppressed slice
  of the same place, and laid back onto that slice by place, since it is one leg. Their
  descriptions, each one check with its code (`tendon_code`):
  1. front to back lies in its slice's plane, as on a sagittal slice
     (abstain_front_to_back_runs_through_the_plane);
  2. fat is not suppressed: with it the band is not uniformly dark over the light's reach, and the
     tendons are laid on from the slice of the same place without it, onto the places nothing
     holds but the fat pads, the border between the lens's regions included
     (abstain_not_uniformly_dark_with_fat_suppression);
  3. the slice names the patella and the tibia, the band's two ends; the patella is named by its
     light only with fat suppression, so here it is the one laid on from the partner
     (abstain_no_patella_and_tibia);
  4. the band is the largest of the slice's dark bands reaching within `SHELL_MM` of both the
     patella and the tibia (`band_joining`); the patellar tendon is its stretch below the
     patella's lowest place along the leg, the quadriceps tendon its stretch above the patella's
     highest, each where no part holds it but the two fat pads beside the patella, which are the
     rest of the patella's territory outside every part named (`extensor_tendons`)
     (abstain_no_dark_band_below_the_patella; abstain_no_dark_band_above_the_patella).
  They relate to none of the twelve categories directly: Hoffa's fat pad lies behind the patellar
  tendon, and the suprapatellar recess, where Effusion's fluid gathers, behind the quadriceps
  tendon. Seen also on the proof: the band's stretch along the patella's front, the fibres that
  pass over it from one tendon to the other, is named neither; the quadriceps tendon's layers are
  named together, with the line of fat between them, just above the patella, where that line is
  narrower than the light's reach, and higher up, where it is wider, its thin front layer is not
  reached; the picture's top edge cuts it; laid onto the fat-suppressed slice, where the band is
  thinner, the patellar tendon takes in up to 1.5 mm of Hoffa's fat behind it.
- FAT UNDER THE SKIN: the subcutaneous fat, with muscle «the rest» of the field: fat is «high on
  T1W, intermediate on T2W» and «low/intermediate» with fat suppression, on the same row as yellow
  marrow, and Hoffa's fat pad «follows the signal of subcutaneous fat on all pulse sequences»
  (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's T1 coronal, 2026-10-15: down each side of
  the knee a bright band under the skin, from the skin's dark rim to the fascia's thin dark line
  on the outer side and to the grey muscle on the inner, x0.75 to x1.9 of the femur's marrow light,
  brightest beside the coil, the muscle about x0.3 to x0.6. The lens's territories cut across the
  band, and on that slice draw the air into themselves, so it names no skin of its own; the
  fat-suppressed coronal of the same place names the air and the skin, and there the fat is grey,
  as dark as muscle. So the skin is laid onto the T1 from it, and the fat is named on the T1 by its
  light and laid back. Its descriptions, each one check with its code (`subcutaneous_code`):
  1. fat is not suppressed: with it the fat is grey, as dark as muscle, and it is laid on from the
     slice of the same place without fat suppression
     (abstain_fat_as_dark_as_muscle_with_fat_suppression);
  2. the slice names the skin, its own or laid on from the other sequence's slice of the same place
     (abstain_no_skin);
  3. the slice names the femur, whose marrow's light the fat's is read against (abstain_no_femur);
  4. it is the places outside every part named at least `LIKE_THE_FEMUR`'s lower bound of the
     femur's marrow light, the pieces of them reaching within `SHELL_MM` of the skin
     (`fat_under_the_skin`) (abstain_no_fat_under_the_skin). Both numbers are borrowed, read on
     the proof by Claude: fat and yellow marrow share a row of [Kh]'s table, so without fat
     suppression the fat is about as bright as marrow, and only the lower bound of the patella's
     tolerance is used, since beside the coil the fat is nearly twice the marrow's light;
     `SHELL_MM`, written for a ligament's reach to its bone, here stands for the skin's dark rim,
     2 to 3 pixels between the air and the fat on the proof's T1 coronal.
  It relates to none of the twelve categories directly. Seen also on the proof: it stops at the
  fascia's thin dark line and leaves the deep fat behind it; a pixel of the band under three
  quarters of the marrow's light is left out; laid onto the fat-suppressed coronal it lies on that
  slice's grey layer under the skin, leaving the layer's outer 1.5 mm to the skin's rim; the T2
  sagittal names no skin, nor does its partner, so there it abstains.
- MUSCLE: with the fat under the skin «the rest» of the field: muscle is «intermediate» on T1W
  and T2W and «low» on proton density, darker than fat and yellow marrow, and «low/intermediate»,
  as grey as fat, with fat suppression (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's T1
  coronal, 2026-10-15: three grey bellies, the vastus medialis above the inner condyle, a belly
  between the outer fat band and the femur, and one beside the tibia below the outer plateau, about
  x0.3 to x0.6 of the femur's marrow light, between the fat, x0.75 and up, and the tendons, the
  bones' shells and the fascia's lines, darker still and millimetres thin. On the proof's sagittal
  without fat suppression the muscles behind the knee are darker, under x0.3 of the marrow, so of
  their light only "darker than fat" holds on every sequence without fat suppression. Fluid is
  darker than fat too on T1 («low»), so by its light alone a body of fluid, a Baker's cyst among
  them, would be named muscle; with fat suppression on a fluid-sensitive sequence fluid is white
  and muscle grey. So muscle is named once the slice is read with its partner, the other
  sequence's slice of the same place, and where that partner is fat-suppressed and
  fluid-sensitive, the places it sees white are left out (a side note of 2026-10-15 asked how
  fluid stays out of muscle). Its descriptions, each one check with its code (`muscle_code`):
  1. fat is not suppressed: with it the muscle is as grey as the fat, and it is laid on from the
     slice of the same place without fat suppression
     (abstain_as_grey_as_fat_with_fat_suppression);
  2. the slice names the air, its own or laid on from the other sequence's slice of the same place,
     so the leg is known (abstain_no_air);
  3. the slice names the femur, whose marrow's light the fat's is read against (abstain_no_femur);
  4. it is the leg's places, neither air nor the black margin, outside every part named, darker
     than fat (under `LIKE_THE_FEMUR`'s lower bound of the femur's marrow light), the bodies of
     them at least `MUSCLE_MM` across (`muscle_bodies`, `thick_parts`); then outside the white the
     fat-suppressed, fluid-sensitive slice of the same place sees as fluid (`white_as_fluid`, laid
     on by place), left out once the bodies are found, since a vessel or a pocket of fluid inside
     a belly does not make the belly thinner (abstain_no_muscle_body).
  It relates to none of the twelve categories directly; the medial gastrocnemius head, a muscle the
  back of the knee's rule names on the axial, borders Baker's cyst. Seen also on the proof: a
  belly's narrow ends, under `MUSCLE_MM` across, are not reached, and its outline is rounded where
  it narrows; laid onto the fat-suppressed coronal it lies on that slice's grey bellies; the
  sagittal without fat suppression names no air, so there it abstains. Where no fat-suppressed,
  fluid-sensitive slice of the same place is read, or beyond its picture, nothing tells fluid
  apart, and a body of fluid darker than fat, a Baker's cyst among them, may be named muscle.
- MEDIAL GASTROCNEMIUS HEAD: the inner head of the calf's big muscle, which arises from the back of
  the femur's medial condyle; «muscle intermediate»; a Baker's cyst lies «between the medial
  gastrocnemius head and the semimembranosus tendon», and medicine reads the back of the knee on
  the fat-suppressed axial (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's fat-suppressed
  axial, 2026-10-15: behind the femur's inner condyle, the muscle's big grey body, the popliteal
  vessels on its outer side and, on its inner side, a thin dark line, its fascia, beyond which lie
  the dark fat of the knee's back-inner corner and the round dark tendons in it. With fat
  suppressed the fat between the muscles is dark, and the lens draws the muscle as a region of its
  own with its peak in the muscle, and the condyle, with the corner's fat, as another; without it
  the fat is bright and draws no border: on the proof's T1 coronal, behind the condyles, the lens
  draws the two heads and the fat between them as one region. It is named on the axial's middle
  slice, whose lens the run has already read, by these descriptions, each one check with its code
  (`gastrocnemius_code`):
  1. the leg runs through its slice's plane, as on an axial slice, where the muscles of the back
     of the knee are cut across (abstain_leg_runs_in_the_plane);
  2. the header names the knee, so its inner side is known (abstain_header_names_no_knee);
  3. fat is suppressed, so the fat between the muscles is dark and the lens draws each muscle as a
     body of its own (abstain_not_parted_from_the_fat_without_fat_suppression);
  4. the femur and the tibia named on the study's middle slices where the leg runs in the plane
     are carried here by place, since it is one leg (`places_on_slice`); the regions the lens draws
     that hold their places are the bones' regions here (abstain_no_bone_carried);
  5. the notch, where the middle sagittal slice passes, parts the knee's inner side from its outer
     (abstain_no_middle_sagittal_slice);
  6. the bone's inner condyle is the bones' region with the deepest peak on the knee's inner side
     of the notch (`inner_condyle`) (abstain_no_inner_condyle);
  7. its body is the region the lens draws, not the bones', whose peak lies on the knee's inner
     side of the notch and behind the inner condyle's peak; the deepest such
     (`gastrocnemius_head`) (abstain_no_body_behind_the_inner_condyle).
  It relates to Baker's: the cyst lies between it and the semimembranosus tendon. Seen also on the
  proof: the region takes in the popliteal vessels on its outer side, the tissue behind the notch
  above it, and a thin strip under the skin along the back of the leg; the lateral head, the same
  body on the knee's outer side, the lens draws as a region of its own, and it is not named.
- SEMIMEMBRANOSUS TENDON: the inner hamstring's tendon, which ends on the back-inner top of the
  tibia: «The direct arm attached to the proximal aspect of the posteromedial part of the tibia
  ... The attachment was posterior to the medial tibial crest and distal to the posteromedial
  aspect of the joint line» (LaPrade et al. 2007, the medial knee); tendons are low on every
  sequence, and a Baker's cyst lies between it and the medial gastrocnemius head
  (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof, 2026-10-15: on the innermost T2 sagittal
  slices a dark cord comes down behind the medial condyle and swells into a dark mass on the back
  of the tibia's top, just below the joint; followed from there onto the fat-suppressed axial, it
  is the black oval at the back-inner corner of the tibia's top, with the semitendinosus, a
  smaller black oval, behind it and the medial gastrocnemius head behind both. On the axial middle
  slice, 21 mm above the joint, its look does not tell it from its neighbours, so it is named on a
  slice of its own by these descriptions, each one check with its code (`semimembranosus_code`):
  1. the leg runs through its slice's plane, as on an axial slice (abstain_leg_runs_in_the_plane);
  2. the header names the knee, so its inner side is known (abstain_header_names_no_knee);
  3. the femur and the tibia named on the study's middle slices where the leg runs in the plane
     are carried onto the axial slices by place, since it is one leg (abstain_no_bone_carried);
  4. the notch, where the middle sagittal slice passes, gives the knee's inner side
     (abstain_no_middle_sagittal_slice);
  5. its slice is the top of the tibia, just below the joint line: of the axial slices that hold
     the tibia's carried places and none of the femur's, below every slice that holds the femur's,
     the highest along the leg (`tibia_top_slice`) (abstain_no_tibia_below_the_femur);
  6. the tibia's inner condyle is found there as for the medial head (`inner_condyle`)
     (abstain_no_inner_condyle);
  7. it is the low signal outside every named part, its cracks one pixel wide closed (the
     scanner's grain lifts some of the tendon's pixels just above the lens's level, so the lens
     draws it cracked), a piece of it at least `MENISCUS_THICKNESS_MM` thick (a tendon cut across;
     a shell or a fascia line is thinner), whose middle lies inside the inner condyle's peak and
     behind it, the back-inner corner, and that reaches within `SHELL_MM` of the condyle's region;
     the front one, since the semitendinosus lies behind it (`semimembranosus_on_slice`)
     (abstain_no_tendon_at_the_back_inner_corner). The condyle's
     region is the one the lens draws round the bone, and on the proof it takes in the whole top
     of the knee, soft tissue too, so that reach keeps the piece at the knee; it does not show the
     piece touching the bone.
  Where one sequence's slice finds no tendon there, it is laid on from the other sequence's slice
  of the same place, as the ACL and the LCL are. It relates to
  Baker's: the cyst lies between it and the medial gastrocnemius head. Seen also on the proof:
  followed from its piece onto the two sagittals, it lies just behind the joint line's back end,
  on the cord that runs down behind the tibia to the insertion, behind the medial meniscus's back
  horn and outside it; it is the black oval there, about 7 by 4 mm, light 0 to 42, and the lens
  marks it to 21, so its grain cracks it, and with the cracks closed the oval is named whole but
  for its narrow tip toward the tibia's back shell, which the rubbing-away takes; two dark bodies
  that touch, or lie a pixel or two apart, are read as one; the PCL's
  end on the back of the tibia lies inside the notch but outside the condyle's peak, and is not
  taken; the medial gastrocnemius head shows on its slice too and is named only on the middle
  slice.
- MENISCI: on a coronal slice, the dark triangles at the two ends of the joint, between the femur's
  condyle and the tibia's plateau («an isosceles triangle on coronal images», low on every
  sequence: docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's fat-suppressed coronal,
  2026-10-14; on its T1 coronal the joint's dark band is not measured low signal, so there they
  are laid on from the fat-suppressed slice of the same place. Their descriptions, each one check
  with its code (`meniscus_code`, `side_code`):
  1. side to side lies in its slice's plane, as on a coronal slice; the middle sagittal slice,
     which side to side runs through, passes through the notch, where the joint holds the
     cruciate ligaments (abstain_side_to_side_runs_through_the_plane);
  2. the slice names the joint (abstain_no_joint);
  3. they are the low signal with every part thinner than `MENISCUS_THICKNESS_MM` rubbed away (the
     bones' thin shells), the pieces of it that touch the joint, each whole, since a meniscus
     reaches out past the bones' ends, and the piece nearest each end, either side of the joint's
     middle (`end_pieces`) (abstain_no_thick_low_signal_in_the_joint);
  4. the medial is the one toward the other knee: where a meniscus is named there is a side to
     read (abstain_no_meniscus), and where the header names the knee (Laterality "R" or "L"; the
     proof study says "R"), the side follows from the patient's left axis (`meniscus_side`);
     where it does not, they stay unsided (abstain_header_names_no_knee).
  The medial meniscus relates to the Medial Meniscus category, Medial OA, and the MCL, which is
  attached to it; the lateral to the Lateral Meniscus category and Lateral OA.
- FIBULA: the bone under the tibia's outer back. Its head has the tibia's marrow, so it is as
  bright as the tibia, and it lies about 5 cm below the tibia's top (seen on the proof's T1 coronal
  and T2 sagittal, 2026-10-14; Rohan: «Do you not see the giant fucking bone that is the
  fibula?»). It is named on its main slice: the squint points to where it must be (`fibula_block`:
  below the tibia's top, on the outer side), the interiors lens reads only that block on each slice
  that holds it, and its main slice is the one where its region is largest (`main_slice`). Its
  descriptions, each one check with its code (`fibula_code`):
  1. the header names the knee, so its outer side is known (abstain_header_names_no_knee);
  2. the middle slice names the tibia (abstain_no_tibia);
  3. fat is not suppressed: with it the marrow is darkened to the light of muscle
     (abstain_marrow_suppressed_with_the_fat);
  4. it is the region the lens draws there that looks like the tibia (within `LIKE_THE_TIBIA` of
     its light), at least a disc `BONE_MM` across, its middle at least `FIBULA_BELOW_MM` below the
     tibia's top and behind the tibia's middle, apart from the tibia and whole in the block
     (`fibula_on_slice`) (abstain_no_bone_like_the_tibia_below_it).
  It relates to Fracture. Seen right on the proof's T2 sagittal, 2026-10-14: slice 30, the bone
  under the tibia's outer condyle, its head and neck.

TWO SLICES OF ONE PLACE (`with_partner`). A study images the knee in two sequences on the same
slices: on the proof, the two sagittals lie on the same planes within 0.002 mm and the two coronals
too, each pair at its own pixel size (measured through the import, 2026-10-14). It is one leg, so
an object found in one is the same object in the other (Rohan, 2026-10-14: «It's literally the same
leg, obviously the object would be the same in both views. That's the WHOLE thesis»), and each
sequence shows what the other may not («If it's visible in one lens but not the other (like "joint
fluid")...then great, we know how to find it, problem solved»). On the proof's
T1 coronal the joint's band is not dark enough for the low-signal lens, so the femur's and tibia's
territories run over the joint and its menisci; on its fat-suppressed coronal they do not. So a
slice is read with its partner, the other sequence's slice of the same place, their places matched
once (`places_from`) and every reading laid across by that match (`laid_by`): a bone
both name is named where both agree, and not at all where they share no place; a part only the
partner names is laid on from it, onto this slice's own interiors that nothing else holds, the
patella only where it holds this slice's own peak in front of the femur; and the joint is again
what lies between the bones.

WHAT THE RULES ON A SLICE SHARE. The founder, 2026-10-15: «Compute that resolved one object of the
knee's anatomy OBVIOUSLY can help resolve the others». Every rule on a slice reads its field
(`read_field`): the leg, the air and the skin, the territories' peaks and which way the slice
faces, read once; a part named on a slice of its own reads only that. What several rules weigh a
place against, the marrow's light over a bone's places, each place's distance from a part, its
position along the patient's axes and each region's size, is the slice's shared measure
(`Measures`): read once on the slice when the first rule asks and handed to every rule after it,
each making and each handing-on counted on the ledger (`knee.telemetry.once`). It is kept by the
places it was read over, so a rule that asks once a part's places have changed (a meniscus may take
some of a bone's) reads it again over the places as they then stand.

The leg runs along the patient's superior axis, front to back along the anterior axis, and side to
side along the left axis, all read from the slice's own frame. Where the leg's axis does not lie in
the plane (an axial slice), the femur, tibia and joint are not named, and the bones of the slices
where it does lie are carried there by place to name the back of the knee; where the side-to-side
axis does not (a sagittal slice), the menisci are not; where the front-to-back axis does not (a
coronal slice), the patella is not. The black margin the reconstruction never filled is outside
the picture, so nothing is named in it. Nothing here draws; the run's renderer draws what this
returns.
"""

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import TypeVar

import numpy as np
from scipy import ndimage as ndi

from knee.collapse.physical import PlaneFrame
from knee.compute.contracts import handed_on
from knee.objects.interiors import InteriorReading
from knee.receipt import digest
from knee.telemetry import once

T = TypeVar("T")

# More along the leg than across it: the cosine of 45 degrees. Geometry.
ALONG_THE_LEG = float(np.sqrt(0.5))
# Air around a leg is a field centimetres across; the picture's edge strips are millimetres.
AIR_FIELD_MM = 10.0
# A bone's shell along the joint is about a millimetre thick; a meniscus is about 5 mm at its base.
# Claude's reading of the proof's fat-suppressed coronal, 2026-10-14.
MENISCUS_THICKNESS_MM = 2.0
# A bone is at least a centimetre across: a region smaller than a disc this wide is not one.
BONE_MM = 10.0
# A muscle's belly about the knee is centimetres across (the vasti, the hamstrings, the
# gastrocnemius, the tibialis anterior); its tendons, the fascia and the vessels among the muscles
# are millimetres (anatomy). Claude's reading of the proof's T1 coronal, 2026-10-15: of the places
# darker than fat, the bodies at least 10 mm across are the three grey bellies on the slice, and at
# 5 mm the round tendons beside the joint's inner side come in too.
MUSCLE_MM = 10.0
# The fibula's marrow is the tibia's tissue, so on one slice it is about as bright: within a
# quarter of the tibia's light. Its head lies under the tibia's plateau, at least 3 cm below the
# tibia's top. Claude's reading of the proof's T2 sagittal, 2026-10-14: the head is x1.00 to x1.08
# of the tibia's light and about 5 cm below its top; the muscle beside it is x0.1 to x0.6.
LIKE_THE_TIBIA = (0.75, 1.33)
FIBULA_BELOW_MM = 30.0
# The patella's marrow is the femur's tissue, so on one slice it is about as bright: within a
# quarter of the femur's light, as the fibula is of the tibia's. It rides on the femur's lower end
# and is about 5 cm tall, so its middle lies in front of the femur and no higher than 5 cm above the
# femur's lowest place on the slice. Claude's reading of the proof's fat-suppressed sagittal,
# 2026-10-14: the patella x0.75 to x1.33 of the femur's light, the fat pad below it x1.5 to x2.5;
# its peak 15 mm in front of the femur and 23 mm above the femur's lowest place.
LIKE_THE_FEMUR = (0.75, 1.33)
PATELLA_ABOVE_MM = 50.0
# Articular cartilage is 2 to 3 mm thick on the femoral condyles and the tibial plateau (anatomy);
# with fat suppression it is clearly brighter than the suppressed marrow beneath it. Claude's
# reading of the proof's fat-suppressed coronal, 2026-10-14: the cartilage x2.4 to x3.5 of the
# marrow's light, the marrow's own speckle within x0.7 to x1.3.
CARTILAGE_MM = 3.0
CARTILAGE_BRIGHTER = 1.5
# A ligament is «uniformly low-signal»: dark over a small area, not speckle by speckle, so its
# light is read as the median over 2 mm. The PCL is about 6 mm thick front to back (anatomy); a
# bone's dark shell is about a millimetre, so a band at least 3 mm thick is not a shell, and a
# ligament attached to a bone lies within 2 mm of its marrow. Claude's reading of the proof's T2
# sagittal, 2026-10-14: the PCL x0.05 to x0.25 of the marrow's light; the fat and fluid of the
# notch x0.5 to x1.4.
LIGAMENT_SMOOTH_MM = 2.0
LIGAMENT_DARKER = 0.3
LIGAMENT_THICK_MM = 3.0
SHELL_MM = 2.0
# The LCL attaches on the outer side of the fibula's head, 8.2 mm (6.8 to 9.7) behind its front
# edge, and on the femur slightly above (1.4 mm) and behind (3.1 mm) the lateral epicondyle; it is
# 69.6 mm long (LaPrade, Ly, Wentorf and Engebretsen, Am J Sports Med 2003, ten knees).
LCL_BEHIND_MM = 8.2
# With fat suppression on a fluid-sensitive sequence fluid is «very high», above cartilage, fat and
# muscle, which are intermediate to low, and above suppressed marrow, which is very low [Kh]. So
# fluid is the white at least four times as bright as the bones' marrow: Claude's reading of the
# proof's fat-suppressed coronal and sagittal, 2026-10-15, where the joint's fluid is x4 to x8 of
# the marrow's light, the cartilage x2.4 to x3.5, and muscle and fat x1 to x2.
FLUID_BRIGHTER = 4.0
# What a slice's codes say when an object is named on it, by its own lens or with its partner's.
NAMED = ("identified", "agreed_with_its_partner", "laid_from_its_partner")
# A place of one slice that lies outside its partner's picture, where the partner has no say.
UNSEEN = -1
BONES = ("femur", "tibia")
MENISCI = ("meniscus", "medial_meniscus", "lateral_meniscus")
OBJECT_CODES = {
    "unassigned": 0,
    "air": 1,
    "skin": 2,
    "femur": 3,
    "tibia": 4,
    "joint": 5,
    "patella": 6,
    "meniscus": 7,
    "medial_meniscus": 8,
    "lateral_meniscus": 9,
    "fibula": 10,
    "femoral_cartilage": 11,
    "tibial_cartilage": 12,
    "pcl": 13,
    "acl": 14,
    "mcl": 15,
    "lcl": 16,
    "joint_fluid": 17,
    "hoffa_fat_pad": 18,
    "suprapatellar_fat": 19,
    "medial_gastrocnemius": 20,
    "semimembranosus": 21,
    "patellar_tendon": 22,
    "quadriceps_tendon": 23,
    "subcutaneous_fat": 24,
    "muscle": 25,
    "synovium": 26,
    "anterior_synovial_recess": 27,
}
CARTILAGES = ("femoral_cartilage", "tibial_cartilage")
# The parts a slice's naming gives a code for (`assign_plane`), in the order it gives them; a part
# named on a slice of its own says of each of them that it is not named there.
SLICE_PARTS = (
    "air",
    "skin",
    "femur",
    "tibia",
    "joint",
    "patella",
    "meniscus",
    "meniscus_side",
    "cartilage",
    "pcl",
    "patellar_tendon",
    "quadriceps_tendon",
    "mcl",
    "joint_fluid",
    "hoffa_fat_pad",
    "suprapatellar_fat",
    "subcutaneous_fat",
    "muscle",
    "anterior_synovial_recess",
    "synovium",
)
FOUR_NEIGHBOURS = ndi.generate_binary_structure(2, 1)


@dataclass(frozen=True, slots=True)
class Peak:
    """One territory's strongest interior peak: where it is, how deep, and how far superior."""

    territory: int
    depth_mm: float
    peak_rc: tuple[int, int]
    superior_mm: float


@dataclass(frozen=True, slots=True)
class PlaneAssignment:
    """The named objects (`OBJECT_CODES`), each object's code, and the peaks they were read from;
    the slice's thick, uniformly dark bands (`dark_bands`), where the PCL's rule read them, for
    any later part a band names (`extensor_tendons`), so they are read once; with fat suppression
    on a fluid-sensitive sequence, the white the joint's fluid was named from (`white_as_fluid`),
    for the slice of the same place without fat suppression, whose muscle leaves it out, so it too
    is read once; and which of the patient's axes lie in the slice's plane (`axes_in_plane`: side
    to side, front to back, along the leg), read once for every stage that asks which way the
    slice faces."""

    objects: np.ndarray
    codes: dict[str, str]
    peaks: tuple[Peak, ...]
    femur: int | None
    tibia: int | None
    patella: int | None = None
    bands: np.ndarray | None = None
    white: np.ndarray | None = None
    in_plane: tuple[bool, bool, bool] = (False, False, False)


def axes_in_plane(basis_lps: np.ndarray) -> tuple[bool, bool, bool]:
    """Which of the patient's axes lie in a slice's plane, more along it than across (`ALONG_THE_LEG`,
    the cosine of 45 degrees): side to side (left), front to back (posterior), along the leg
    (superior), read from the slice's own frame."""
    unit = basis_lps / np.linalg.norm(basis_lps, axis=0)
    sides, front, leg = (
        float(np.linalg.norm(unit[axis])) >= ALONG_THE_LEG for axis in range(3)
    )
    return sides, front, leg


def margin(plane: np.ndarray) -> np.ndarray:
    """The black margin: stored zeros joined to the picture's frame through zeros."""
    zeros = plane == 0
    if not zeros.any():
        return zeros
    parts, _ = ndi.label(zeros)
    frame = np.concatenate((parts[0], parts[-1], parts[:, 0], parts[:, -1]))
    return np.isin(parts, frame[frame > 0])


def fields(outside: np.ndarray, spacing_rc: np.ndarray) -> np.ndarray:
    """The pieces of `outside` at least `AIR_FIELD_MM` thick (twice their deepest inner distance)."""
    parts, count = ndi.label(outside, structure=np.ones((3, 3), dtype=bool))
    if not count:
        return outside.copy()
    depth = ndi.distance_transform_edt(outside, sampling=spacing_rc)
    thickest = ndi.maximum(depth, parts, index=np.arange(1, count + 1))
    keep = np.flatnonzero(2.0 * np.asarray(thickest) >= AIR_FIELD_MM) + 1
    return np.isin(parts, keep)


def territory_peaks(
    labels: np.ndarray, distance_mm: np.ndarray, basis_lps: np.ndarray
) -> tuple[Peak, ...]:
    """Every territory's strongest interior peak, the deepest first."""
    found = []
    for territory in range(1, int(labels.max(initial=0)) + 1):
        mask = labels == territory
        if not mask.any():
            continue
        depth = float(distance_mm[mask].max())
        row, col = np.argwhere(mask & (distance_mm == depth))[0]
        superior = float(basis_lps[2] @ np.asarray((row, col), dtype=np.float64))
        found.append(Peak(territory, depth, (int(row), int(col)), superior))
    return tuple(sorted(found, key=lambda peak: peak.depth_mm, reverse=True))


def along_the_leg(basis_lps: np.ndarray, a_rc, b_rc) -> float:
    """How much of the way from a to b runs along the leg (the patient's superior axis), 0 to 1."""
    step = np.asarray(b_rc, dtype=np.float64) - np.asarray(a_rc, dtype=np.float64)
    way = basis_lps @ step
    length = float(np.linalg.norm(way))
    return abs(float(way[2])) / length if length else 0.0


def pair_code(leg_in_plane: bool, territories: int, partner_found: bool) -> str:
    """Whether the femur and tibia were named, or why not."""
    if not leg_in_plane:
        return "abstain_leg_runs_through_the_plane"
    if territories < 2:
        return "abstain_fewer_than_two_territories"
    if not partner_found:
        return "abstain_nothing_above_or_below_the_deepest"
    return "identified"


def meniscus_code(sides_in_plane: bool, joint_named: bool, found: int) -> str:
    """Whether menisci were named, or why not."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not joint_named:
        return "abstain_no_joint"
    if not found:
        return "abstain_no_thick_low_signal_in_the_joint"
    return "identified"


def meniscus_side(knee: str, toward_left: bool) -> str:
    """Which meniscus a piece is: "medial", "lateral", or "meniscus" when the knee is not named.

    The medial meniscus lies on the side toward the other knee. For a right knee that is the
    patient's left; for a left knee, the patient's right. `knee` is the header's own word, "R" or
    "L"; `toward_left` says whether the piece is at the joint's end toward the patient's left.
    """
    if knee not in ("R", "L"):
        return "meniscus"
    return "medial" if toward_left == (knee == "R") else "lateral"


def side_code(knee: str, named: int) -> str:
    """Whether the menisci's sides were read, or why not."""
    if not named:
        return "abstain_no_meniscus"
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    return "from_the_header"


def cartilage_code(
    sides_in_plane: bool, fat_suppressed: bool, joint_named: bool, found: bool
) -> str:
    """Whether the articular cartilage was named, or why not."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not fat_suppressed:
        return "abstain_not_brighter_than_marrow_without_fat_suppression"
    if not joint_named:
        return "abstain_no_joint"
    if not found:
        return "abstain_nothing_bright_against_the_bones"
    return "identified"


def marrow_light(plane: np.ndarray, bone: np.ndarray) -> float:
    """The marrow's light on a slice: the median of the plane over a bone's places (the femur's,
    or the femur's and the tibia's together). The one statement of it, read once on a slice and
    handed to every rule that weighs a place against it."""
    return float(np.median(plane[bone]))


def distance_from(places: np.ndarray, spacing_rc: np.ndarray) -> np.ndarray:
    """Each place's distance in millimetres from the given places, a part's: the one statement of a
    reach to a part, which every rule that measures one reads (through `Measures.distance`, once on
    a slice)."""
    return np.asarray(ndi.distance_transform_edt(~places, sampling=spacing_rc))


def positions_along(
    shape: tuple[int, int], basis_lps: np.ndarray, axis: int
) -> np.ndarray:
    """Each place's position along one of the patient's axes (0 toward the left, 1 toward the back,
    2 toward the head), in millimetres from the slice's first pixel: the one statement of it, which
    every rule that sides a place or orders it along the leg reads (through `Measures.along`)."""
    rows, cols = np.indices(shape)
    return basis_lps[axis, 0] * rows + basis_lps[axis, 1] * cols


def region_sizes(labels: np.ndarray) -> np.ndarray:
    """How many places each region the lens draws holds, by its label, 0 for the places no region
    holds: the one statement of it, which every rule that weighs a region by its size reads
    (through `Measures.sizes`)."""
    return np.bincount(labels.ravel())


@dataclass(frozen=True, slots=True)
class Measures:
    """What the rules on one slice weigh a place against, read once on the slice and handed to every
    rule that asks for it (`knee.telemetry.once`, each making and each handing-on counted on the
    ledger): the marrow's light over a bone's places (`marrow_light`), each place's distance from a
    part's places (`distance_from`), its position along each of the patient's axes
    (`positions_along`), and the size of each region the lens draws (`region_sizes`).

    `key` names the slice: its series and index. A value is kept under it with what it was read
    from, the places by their digest and a distance's pixel size too, so a rule that asks after a
    part's places have changed (a meniscus may take some of a bone's, a partner may lay its own on)
    reads it again, and one that asks over the same places is handed the value already read. A
    kept array is frozen (`handed_on`), since every rule that asks is handed the same one. Without
    a key nothing is kept, and each is read where it is asked for, as a test or a single call
    needs.
    """

    key: Hashable | None
    plane: np.ndarray
    basis_lps: np.ndarray

    def _kept(self, kind: str, inputs: Hashable, make: Callable[[], T]) -> T:
        return make() if self.key is None else once(kind, (self.key, inputs), make)

    def light(self, places: np.ndarray) -> float:
        """The marrow's light over a bone's places (`marrow_light`)."""
        return self._kept(
            "light", digest(places), lambda: marrow_light(self.plane, places)
        )

    def distance(self, places: np.ndarray, spacing_rc: np.ndarray) -> np.ndarray:
        """Each place's distance from a part's places, at the given pixel size (`distance_from`)."""
        size = tuple(float(step) for step in np.asarray(spacing_rc))
        return self._kept(
            "distance",
            (digest(places), size),
            lambda: handed_on(distance_from(places, spacing_rc)),
        )

    def along(self, axis: int) -> np.ndarray:
        """Each place's position along one of the patient's axes (`positions_along`)."""
        return self._kept(
            "position",
            axis,
            lambda: handed_on(positions_along(self.plane.shape, self.basis_lps, axis)),
        )

    def sizes(self, labels: np.ndarray) -> np.ndarray:
        """How many places each region the lens draws holds (`region_sizes`)."""
        return self._kept(
            "sizes", digest(labels), lambda: handed_on(region_sizes(labels))
        )


def cartilage_on(
    plane: np.ndarray,
    objects: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """The articular cartilage on one slice, femoral and tibial: in the joint, the places brighter
    than the bones' marrow by `CARTILAGE_BRIGHTER`, within `CARTILAGE_MM` of the femur or the tibia,
    each named for the nearer bone. Both empty where the slice names no femur, tibia or joint.
    `measures` are the slice's shared measures, when its caller keeps them: the bones' marrow light
    and each place's distance from the femur and from the tibia are read from them."""
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    joint = objects == OBJECT_CODES["joint"]
    none = np.zeros(plane.shape, dtype=bool)
    if not (femur.any() and tibia.any() and joint.any()):
        return none, none
    bones = femur | tibia
    light = marrow_light(plane, bones) if measures is None else measures.light(bones)
    if light <= 0:
        return none, none
    if measures is None:
        to_femur = distance_from(femur, spacing_rc)
        to_tibia = distance_from(tibia, spacing_rc)
    else:
        to_femur = measures.distance(femur, spacing_rc)
        to_tibia = measures.distance(tibia, spacing_rc)
    bright = joint & (plane > CARTILAGE_BRIGHTER * light)
    femoral = bright & (to_femur <= CARTILAGE_MM) & (to_femur <= to_tibia)
    tibial = bright & (to_tibia <= CARTILAGE_MM) & (to_tibia < to_femur)
    return femoral, tibial


def pcl_code(
    front_to_back_in_plane: bool, fat_suppressed: bool, bones_named: bool, found: bool
) -> str:
    """Whether the PCL was named, or why not."""
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if fat_suppressed:
        return "abstain_marrow_as_dark_as_a_ligament_with_fat_suppression"
    if not bones_named:
        return "abstain_no_femur_and_tibia"
    if not found:
        return "abstain_no_dark_band_joins_the_bones"
    return "identified"


def dark_bands(
    plane: np.ndarray,
    objects: np.ndarray,
    spacing_rc: np.ndarray,
    outside_picture: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The slice's thick, uniformly dark bands, each piece its own label (0 elsewhere): the places
    whose light over `LIGAMENT_SMOOTH_MM` is under `LIGAMENT_DARKER` of the femur's marrow, outside
    the femur, the tibia and the black margin (`outside_picture`, from `margin`; a stored zero
    inside the leg is the darkest tissue, not the margin), at least `LIGAMENT_THICK_MM` thick. All
    zero when the slice names no femur, or its light is none. `measures` are the slice's shared
    measures, when its caller keeps them: the femur's marrow light is read from them."""
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    none = np.zeros(plane.shape, dtype=np.int32)
    if not femur.any():
        return none
    light = marrow_light(plane, femur) if measures is None else measures.light(femur)
    if light <= 0:
        return none
    size = tuple(int(2 * round(LIGAMENT_SMOOTH_MM / step) + 1) for step in spacing_rc)
    uniform = ndi.median_filter(np.asarray(plane, dtype=np.float64), size=size)
    dark = (uniform < LIGAMENT_DARKER * light) & ~outside_picture & ~femur & ~tibia
    pieces, _ = ndi.label(thick_parts(dark, spacing_rc, LIGAMENT_THICK_MM))
    return np.asarray(pieces, dtype=np.int32)


def band_joining(
    bands: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """Of the dark bands (`dark_bands`), the largest reaching within `SHELL_MM` of both `first` and
    `second`, two named parts. Empty when none does. `measures` are the slice's shared measures,
    when its caller keeps them: each place's distance from the two parts is read from them."""
    none = np.zeros(bands.shape, dtype=bool)
    count = int(bands.max(initial=0))
    if not count or not (first.any() and second.any()):
        return none
    if measures is None:
        near_first = distance_from(first, spacing_rc)
        near_second = distance_from(second, spacing_rc)
    else:
        near_first = measures.distance(first, spacing_rc)
        near_second = measures.distance(second, spacing_rc)
    labels = np.arange(1, count + 1)
    reach_first = np.asarray(ndi.minimum(near_first, bands, index=labels))
    reach_second = np.asarray(ndi.minimum(near_second, bands, index=labels))
    sizes = np.bincount(bands.ravel(), minlength=count + 1)[1:]
    joining = (reach_first <= SHELL_MM) & (reach_second <= SHELL_MM)
    if not joining.any():
        return none
    return bands == int(labels[joining][np.argmax(sizes[joining])])


def tendon_code(
    front_to_back_in_plane: bool,
    fat_suppressed: bool,
    ends_named: bool,
    found: bool,
    above: bool = False,
) -> str:
    """Whether the patellar tendon (or, `above` the patella, the quadriceps tendon) was named, or why
    not."""
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if fat_suppressed:
        return "abstain_not_uniformly_dark_with_fat_suppression"
    if not ends_named:
        return "abstain_no_patella_and_tibia"
    if not found:
        return (
            "abstain_no_dark_band_above_the_patella"
            if above
            else "abstain_no_dark_band_below_the_patella"
        )
    return "identified"


def subcutaneous_code(
    fat_suppressed: bool, skin_named: bool, femur_named: bool, found: bool
) -> str:
    """Whether the fat under the skin was named, or why not."""
    if fat_suppressed:
        return "abstain_fat_as_dark_as_muscle_with_fat_suppression"
    if not skin_named:
        return "abstain_no_skin"
    if not femur_named:
        return "abstain_no_femur"
    if not found:
        return "abstain_no_fat_under_the_skin"
    return "identified"


def fat_under_the_skin(
    plane: np.ndarray,
    objects: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The fat under the skin on a slice without fat suppression: the places outside every part
    named at least `LIKE_THE_FEMUR`'s lower bound of the femur's marrow light, the pieces of them
    reaching within `SHELL_MM` of the skin. Empty when the slice names no skin or no femur.
    `measures` are the slice's shared measures, when its caller keeps them: the femur's marrow
    light and each place's distance from the skin are read from them."""
    skin = objects == OBJECT_CODES["skin"]
    femur = objects == OBJECT_CODES["femur"]
    none = np.zeros(plane.shape, dtype=bool)
    if not (skin.any() and femur.any()):
        return none
    light = marrow_light(plane, femur) if measures is None else measures.light(femur)
    if light <= 0:
        return none
    pieces, count = ndi.label((plane >= LIKE_THE_FEMUR[0] * light) & (objects == 0))
    if not count:
        return none
    near_skin = (
        distance_from(skin, spacing_rc)
        if measures is None
        else measures.distance(skin, spacing_rc)
    )
    labels = np.arange(1, count + 1)
    reach = np.asarray(ndi.minimum(near_skin, pieces, index=labels))
    return np.isin(pieces, labels[reach <= SHELL_MM])


def muscle_code(
    fat_suppressed: bool, air_named: bool, femur_named: bool, found: bool
) -> str:
    """Whether muscle was named, or why not."""
    if fat_suppressed:
        return "abstain_as_grey_as_fat_with_fat_suppression"
    if not air_named:
        return "abstain_no_air"
    if not femur_named:
        return "abstain_no_femur"
    if not found:
        return "abstain_no_muscle_body"
    return "identified"


def muscle_bodies(
    plane: np.ndarray,
    objects: np.ndarray,
    spacing_rc: np.ndarray,
    outside_picture: np.ndarray,
    white: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """Muscle on a slice without fat suppression: the leg's places (neither air nor the black
    margin, `outside_picture`) outside every part named, darker than fat (under `LIKE_THE_FEMUR`'s
    lower bound of the femur's marrow light), the bodies of them at least `MUSCLE_MM` across
    (`thick_parts`); then outside `white`, the places the fat-suppressed, fluid-sensitive slice of
    the same place sees white as fluid (none where no such slice is read). The white is left out
    after the bodies are found, since a vessel or a pocket of fluid inside a belly does not make
    the belly thinner. Empty when the slice names no air or no femur. `measures` are the slice's
    shared measures, when its caller keeps them: the femur's marrow light is read from them."""
    air = objects == OBJECT_CODES["air"]
    femur = objects == OBJECT_CODES["femur"]
    none = np.zeros(plane.shape, dtype=bool)
    if not (air.any() and femur.any()):
        return none
    light = marrow_light(plane, femur) if measures is None else measures.light(femur)
    if light <= 0:
        return none
    darker = (plane < LIKE_THE_FEMUR[0] * light) & (objects == 0) & ~outside_picture
    return thick_parts(darker, spacing_rc, MUSCLE_MM) & ~white


def extensor_tendons(
    bands: np.ndarray,
    objects: np.ndarray,
    spacing_rc: np.ndarray,
    basis_lps: np.ndarray,
    measures: Measures | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """The patellar and the quadriceps tendon on a sagittal slice: of the dark bands, the one joining
    the patella and the tibia (`band_joining`), the extensor mechanism's; below the patella's lowest
    place along the leg, the patellar tendon, and above its highest, the quadriceps tendon, each
    where no part holds it but the two fat pads beside the patella, which are the rest of its
    territory outside every part named. Alongside the patella it is neither. Both empty when the
    slice does not name the patella and the tibia. `measures` are the slice's shared measures,
    when its caller keeps them: each place's distance from the patella and the tibia, and its
    position along the leg, are read from them."""
    patella = objects == OBJECT_CODES["patella"]
    tibia = objects == OBJECT_CODES["tibia"]
    band = band_joining(bands, patella, tibia, spacing_rc, measures)
    none = np.zeros(objects.shape, dtype=bool)
    if not band.any():
        return none, none
    fat = (OBJECT_CODES["hoffa_fat_pad"], OBJECT_CODES["suprapatellar_fat"])
    open_to_it = band & np.isin(objects, (0, *fat))
    up = (  # mm toward the head
        positions_along(objects.shape, basis_lps, 2)
        if measures is None
        else measures.along(2)
    )
    below = open_to_it & (up < float(up[patella].min()))
    above = open_to_it & (up > float(up[patella].max()))
    return below, above


def acl_code(
    front_to_back_in_plane: bool,
    knee: str,
    bones_carried: bool,
    fat_suppressed: bool,
    found: bool,
) -> str:
    """Whether the ACL was named on its slice, or why not: each check is one of its descriptions."""
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if not bones_carried:
        return "abstain_no_femur_and_tibia_to_carry"
    if not fat_suppressed:
        return "abstain_not_walled_off_without_fat_suppression"
    if not found:
        return "abstain_no_region_in_the_joint"
    return "identified"


def outer_step(knee: str, next_toward_left_mm: float) -> int:
    """Which neighbour of the middle slice lies on the knee's outer side: 1 for the next slice, -1
    for the one before. `next_toward_left_mm` is how far the next slice lies toward the patient's
    left of the middle one; the outer side is the patient's right for a right knee ("R") and the
    patient's left for a left one ("L")."""
    return 1 if (next_toward_left_mm > 0) == (knee == "L") else -1


def carried_bone(
    labels: np.ndarray, before: np.ndarray, measures: Measures | None = None
) -> np.ndarray:
    """A bone carried from the middle slice to a neighbouring one by place, since anatomy is
    contiguous from slice to slice: the regions the lens draws there most of whose places were the
    bone on the middle slice (`before`). Empty when none were. `measures` are the slice's shared
    measures, when its caller keeps them: each region's size is read from them."""
    count = int(labels.max(initial=0)) + 1
    inside = np.bincount(labels[before & (labels > 0)], minlength=count)
    whole = region_sizes(labels) if measures is None else measures.sizes(labels)
    regions = np.flatnonzero(2 * inside > whole)
    return np.isin(labels, regions[regions > 0])


def acl_on_slice(
    labels: np.ndarray,
    peaks: tuple[Peak, ...],
    femur: np.ndarray,
    tibia: np.ndarray,
    basis_lps: np.ndarray,
    outside_picture: np.ndarray,
) -> np.ndarray:
    """The ACL on its slice: the region the lens draws whose peak lies in the joint, between the
    femur and the tibia along the leg; the deepest such. Empty when no region's peak lies there."""
    joint = between_along_the_leg(femur, tibia, basis_lps)
    joint &= ~femur & ~tibia & ~outside_picture
    for peak in peaks:  # the deepest first
        if joint[peak.peak_rc]:
            return labels == peak.territory
    return np.zeros(labels.shape, dtype=bool)


def mcl_code(sides_in_plane: bool, medial_meniscus: bool, found: bool) -> str:
    """Whether the MCL was named, or why not: each check is one of its descriptions."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not medial_meniscus:
        return "abstain_no_medial_meniscus"
    if not found:
        return "abstain_no_low_signal_joins_the_bones_on_the_inner_side"
    return "identified"


def ligament_on_the_inner_side(
    dark: np.ndarray,
    objects: np.ndarray,
    basis_lps: np.ndarray,
    outside_picture: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The MCL on one slice: of the low signal left once the named parts are out, the largest
    piece on the medial meniscus's side of the joint's middle that reaches within `SHELL_MM` of
    both the femur and the tibia. Empty when none does, or when the slice names no medial
    meniscus, no joint, or not both bones. `measures` are the slice's shared measures, when its
    caller keeps them: each place's position toward the left and its distance from the femur and
    from the tibia are read from them, only when a piece needs them."""
    none = np.zeros(dark.shape, dtype=bool)
    medial = objects == OBJECT_CODES["medial_meniscus"]
    joint = objects == OBJECT_CODES["joint"]
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    if not (medial.any() and joint.any() and femur.any() and tibia.any()):
        return none
    left = dark & (objects == 0) & ~outside_picture
    pieces, count = ndi.label(left, structure=np.ones((3, 3), dtype=bool))
    if not count:
        return none
    leftward = (
        positions_along(dark.shape, basis_lps, 0)
        if measures is None
        else measures.along(0)
    )
    middle = float(leftward[joint].mean())  # the joint's middle
    inner = np.sign(float(leftward[medial].mean()) - middle)
    labels = np.arange(1, count + 1)
    spacing_rc = np.linalg.norm(basis_lps, axis=0)
    if measures is None:
        near_femur = distance_from(femur, spacing_rc)
        near_tibia = distance_from(tibia, spacing_rc)
    else:
        near_femur = measures.distance(femur, spacing_rc)
        near_tibia = measures.distance(tibia, spacing_rc)
    side = np.sign(np.asarray(ndi.mean(leftward, pieces, index=labels)) - middle)
    joining = (
        (side == inner)
        & (np.asarray(ndi.minimum(near_femur, pieces, index=labels)) <= SHELL_MM)
        & (np.asarray(ndi.minimum(near_tibia, pieces, index=labels)) <= SHELL_MM)
    )
    if not joining.any():
        return none
    sizes = np.bincount(pieces.ravel(), minlength=count + 1)[1:]
    return pieces == int(labels[joining][np.argmax(sizes[joining])])


def lcl_code(
    sides_in_plane: bool,
    fibula_named: bool,
    bones: bool,
    on_the_slices: bool,
    fat_suppressed: bool,
    fibula_here: bool,
    found: bool,
) -> str:
    """Whether the LCL was named on its slice, or why not: each check is one of its descriptions."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not fibula_named:
        return "abstain_no_fibula"
    if not bones:
        return "abstain_no_femur_and_tibia_to_carry"
    if not on_the_slices:
        return "abstain_attachment_off_the_slices"
    if fat_suppressed:
        return "abstain_not_parted_from_the_fat_with_fat_suppression"
    if not fibula_here:
        return "abstain_no_fibula_on_the_slice"
    if not found:
        return "abstain_no_region_joins_the_femur_and_the_fibula"
    return "identified"


def lcl_attachment(fibula_lps: np.ndarray) -> np.ndarray:
    """Where the LCL attaches on the fibula, in the scanner's millimetres (x toward the patient's
    left, y toward the back, z up): `LCL_BEHIND_MM` behind the front edge of the fibula's places, at
    their middle side to side and up and down."""
    point = np.asarray(fibula_lps, dtype=np.float64).mean(axis=0)
    point[1] = float(np.min(fibula_lps[:, 1])) + LCL_BEHIND_MM
    return point


def slice_through(
    point_lps: np.ndarray,
    origins_lps: np.ndarray,
    normal: np.ndarray,
    thicknesses_mm: list[float],
) -> int | None:
    """The slice of a series whose plane passes within half its thickness of a place; None when none
    does. `origins_lps` (Z, 3) are the slices' origins and `normal` the series' unit normal."""
    offsets = np.abs((np.asarray(point_lps) - np.asarray(origins_lps)) @ normal)
    nearest = int(np.argmin(offsets))
    return nearest if offsets[nearest] <= thicknesses_mm[nearest] / 2.0 else None


def places_on_slice(
    points_lps: np.ndarray,
    frame: PlaneFrame,
    shape: tuple[int, int],
    thickness_mm: float,
) -> np.ndarray:
    """The pixels of a slice holding the given places, those within half its thickness of its plane.
    Places are in the scanner's millimetres; `frame` is the slice's, whose normal and inverse
    (`PlaneFrame.normal`, `PlaneFrame.to_native`) carry them onto it."""
    points = np.asarray(points_lps, dtype=np.float64)
    near = np.abs((points - frame.origin_lps) @ frame.normal()) <= thickness_mm / 2.0
    rc = np.rint(frame.to_native(points[near])).astype(int)
    inside = (
        (rc[:, 0] >= 0)
        & (rc[:, 0] < shape[0])
        & (rc[:, 1] >= 0)
        & (rc[:, 1] < shape[1])
    )
    held = np.zeros(shape, dtype=bool)
    held[rc[inside, 0], rc[inside, 1]] = True
    return held


def region_holding(labels: np.ndarray, places: np.ndarray) -> np.ndarray:
    """The region the lens draws that holds most of the given places; empty when none holds any."""
    held = labels[places & (labels > 0)]
    if not held.size:
        return np.zeros(labels.shape, dtype=bool)
    return labels == int(np.argmax(np.bincount(held)))


def lcl_on_slice(
    labels: np.ndarray,
    femur: np.ndarray,
    fibula: np.ndarray,
    across_mm: np.ndarray,
    tibia_across_mm: float,
    fibula_across_mm: float,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The LCL on its slice: of the regions the lens draws, neither the femur's nor the fibula's,
    those whose middle lies on the fibula's side of the tibia's middle (the knee's outer side) and
    that reach within `SHELL_MM` of both the femur and the fibula; the largest. `across_mm` is each
    place's position toward the patient's left. Empty when none does. `measures` are the slice's
    shared measures, when its caller keeps them: each place's distance from the femur and from the
    fibula, and each region's size, are read from them."""
    none = np.zeros(labels.shape, dtype=bool)
    count = int(labels.max(initial=0))
    if not (count and femur.any() and fibula.any()):
        return none
    index = np.arange(1, count + 1)
    if measures is None:
        to_femur = distance_from(femur, spacing_rc)
        to_fibula = distance_from(fibula, spacing_rc)
        sizes = region_sizes(labels)[1:]
    else:
        to_femur = measures.distance(femur, spacing_rc)
        to_fibula = measures.distance(fibula, spacing_rc)
        sizes = measures.sizes(labels)[1:]
    bone = np.bincount(labels[femur | fibula], minlength=count + 1)[1:] > 0
    middle = np.asarray(ndi.mean(across_mm, labels, index=index))
    outer = np.sign(fibula_across_mm - tibia_across_mm)
    joining = (
        (sizes > 0)
        & ~bone
        & (np.sign(middle - tibia_across_mm) == outer)
        & (np.asarray(ndi.minimum(to_femur, labels, index=index)) <= SHELL_MM)
        & (np.asarray(ndi.minimum(to_fibula, labels, index=index)) <= SHELL_MM)
    )
    if not joining.any():
        return none
    return labels == int(index[joining][np.argmax(sizes[joining])])


def fluid_code(fluid_bright: bool, bones_named: bool, found: bool) -> str:
    """Whether the joint's fluid was named, or why not: each check is one of its descriptions."""
    if not fluid_bright:
        return "abstain_fluid_not_bright_on_this_sequence"
    if not bones_named:
        return "abstain_no_femur_and_tibia"
    if not found:
        return "abstain_no_bright_fluid_in_the_recesses"
    return "identified"


def white_as_fluid(
    plane: np.ndarray, objects: np.ndarray, measures: Measures | None = None
) -> np.ndarray | None:
    """On a fat-suppressed, fluid-sensitive slice, the places white as fluid: more than
    `FLUID_BRIGHTER` times as bright as the bones' marrow, the femur's and the tibia's together.
    None where the slice names no femur and tibia, or their light is none. `measures` are the
    slice's shared measures, when its caller keeps them: the bones' marrow light is read from
    them."""
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    if not (femur.any() and tibia.any()):
        return None
    bones = femur | tibia
    light = marrow_light(plane, bones) if measures is None else measures.light(bones)
    if light <= 0:
        return None
    return plane > FLUID_BRIGHTER * light


def fluid_in_the_recesses(
    white: np.ndarray,
    objects: np.ndarray,
    leg: np.ndarray,
    outside_picture: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The joint's fluid on a fat-suppressed, fluid-sensitive slice: of the places white as fluid
    (`white`, from `white_as_fluid`), those in the leg outside every part named but the joint; of
    their pieces, those that touch the joint or lie within `SHELL_MM` of the femur, the tibia or
    the patella, in the joint's own recesses. `measures` are the slice's shared measures, when its
    caller keeps them: each place's distance from the bones is read from them."""
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    joint = objects == OBJECT_CODES["joint"]
    none = np.zeros(objects.shape, dtype=bool)
    open_places = np.isin(objects, (0, OBJECT_CODES["joint"]))
    bright = white & leg & open_places & ~outside_picture
    eight = np.ones((3, 3), dtype=bool)
    pieces, count = ndi.label(bright, structure=eight)
    if not count:
        return none
    bones = femur | tibia | (objects == OBJECT_CODES["patella"])
    near = (
        distance_from(bones, spacing_rc)
        if measures is None
        else measures.distance(bones, spacing_rc)
    ) <= SHELL_MM
    near |= ndi.binary_dilation(joint, structure=eight)
    held = np.unique(pieces[near & (pieces > 0)])
    return np.isin(pieces, held[held > 0])


def anterior_synovial_recess(
    white: np.ndarray,
    objects: np.ndarray,
    basis_lps: np.ndarray,
    measures: Measures | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """The anterior joint recess and its fat-facing lining surface on a sagittal slice.

    Fluid lies behind the patella/extensor mechanism, in front of the femur, and above the
    patella's lower end (OBJECTS_AND_CONDITIONS, joint cavity and recesses). Of the connected
    white bodies intersecting that place, keep the largest. The anterior half of its boundary
    locates the lining against the fat, avoiding the posterior, articular side. This is a
    surface location sampled on the cavity side, not a measurement of membrane thickness.

    Positions come from the patient's axes and named parts, never study coordinates. The
    supplied white is the existing fluid reading; no intensity threshold is fitted here.
    """
    empty = np.zeros(objects.shape, dtype=bool)
    femur = objects == OBJECT_CODES["femur"]
    patella = objects == OBJECT_CODES["patella"]
    if not (femur.any() and patella.any() and white.any()):
        return empty, empty.copy()
    back = (
        positions_along(objects.shape, basis_lps, 1)
        if measures is None
        else measures.along(1)
    )
    up = (
        positions_along(objects.shape, basis_lps, 2)
        if measures is None
        else measures.along(2)
    )
    pocket = (
        (back > np.median(back[patella]))
        & (back < np.median(back[femur]))
        & (up >= up[patella].min())
        & ~np.isin(
            objects, [OBJECT_CODES[name] for name in (*BONES, "patella", "pcl", "acl")]
        )
    )
    pieces, _ = ndi.label(white, structure=np.ones((3, 3), dtype=bool))
    candidates = np.unique(pieces[pocket & white])
    candidates = candidates[candidates > 0]
    if not candidates.size:
        return empty, empty.copy()
    sizes = np.bincount(pieces.ravel())
    region = int(candidates[np.argmax(sizes[candidates])])
    recess = pieces == region
    boundary = recess & ~ndi.binary_erosion(recess, structure=FOUR_NEIGHBOURS)
    lining = boundary & (back < np.median(back[recess]))
    return recess, lining


def synovium_code(
    sagittal: bool, fluid_bright: bool, patella: bool, femur: bool, recess: bool
) -> str:
    """Why the anterior recess and its fat-facing synovial surface are or are not located."""
    if not sagittal:
        return "abstain_not_a_sagittal_slice"
    if not fluid_bright:
        return "abstain_fluid_not_bright_on_this_sequence"
    if not patella:
        return "abstain_no_patella"
    if not femur:
        return "abstain_no_femur"
    if not recess:
        return "abstain_no_fluid_in_the_anterior_recess"
    return "identified"


def fat_pad_code(
    front_to_back_in_plane: bool,
    fat_suppressed: bool,
    patella_named: bool,
    found: bool,
    above: bool = False,
) -> str:
    """Whether a fat pad beside the patella was named, Hoffa's below it or the suprapatellar fat
    above it (`above`), or why not: each check is one of its descriptions."""
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if not fat_suppressed:
        return "abstain_fat_as_bright_as_marrow"
    if not patella_named:
        return "abstain_no_patella"
    if not found:
        if above:
            return "abstain_nothing_above_the_patella"
        return "abstain_nothing_below_the_patella"
    return "identified"


def rest_of_the_patellas_territory(
    labels: np.ndarray,
    territory: int,
    patella: np.ndarray,
    objects: np.ndarray,
    basis_lps: np.ndarray,
    upward: bool = False,
    measures: Measures | None = None,
) -> np.ndarray:
    """A fat pad beside the patella: the rest of the patella's territory beyond the patella along
    the leg, outside every part named; below its lowest place (Hoffa's), or above its highest when
    `upward` (the suprapatellar fat). Empty when the patella has no places. `measures` are the
    slice's shared measures, when its caller keeps them: each place's position along the leg is
    read from them."""
    if not patella.any():
        return np.zeros(labels.shape, dtype=bool)
    up = (  # mm toward the head
        positions_along(labels.shape, basis_lps, 2)
        if measures is None
        else measures.along(2)
    )
    if upward:
        beyond = up > float(up[patella].max())
    else:
        beyond = up < float(up[patella].min())
    return (labels == territory) & beyond & (objects == 0)


def gastrocnemius_code(
    leg_through_plane: bool,
    knee: str,
    fat_suppressed: bool,
    bone_carried: bool,
    notch: bool,
    condyle: bool,
    found: bool,
) -> str:
    """Whether the medial gastrocnemius head was named, or why not: each check is one of its
    descriptions."""
    if not leg_through_plane:
        return "abstain_leg_runs_in_the_plane"
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if not fat_suppressed:
        return "abstain_not_parted_from_the_fat_without_fat_suppression"
    if not bone_carried:
        return "abstain_no_bone_carried"
    if not notch:
        return "abstain_no_middle_sagittal_slice"
    if not condyle:
        return "abstain_no_inner_condyle"
    if not found:
        return "abstain_no_body_behind_the_inner_condyle"
    return "identified"


def inner_condyle(
    peaks: tuple[Peak, ...], labels: np.ndarray, bone: np.ndarray, inner_mm: np.ndarray
) -> Peak | None:
    """The bone's inner condyle on a slice the leg runs through: of the regions the lens draws that
    hold the bones' places carried there (`bone`), the one with the deepest peak on the knee's
    inner side of the notch (`inner_mm`, each place's distance toward that side). None when no
    bone's region has its peak there."""
    regions = np.unique(labels[bone & (labels > 0)])
    for peak in peaks:  # the deepest first
        if np.isin(peak.territory, regions) and inner_mm[peak.peak_rc] > 0:
            return peak
    return None


def gastrocnemius_head(
    peaks: tuple[Peak, ...],
    labels: np.ndarray,
    bone: np.ndarray,
    condyle: Peak,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
) -> np.ndarray:
    """The medial gastrocnemius head on a slice the leg runs through: of the regions the lens draws
    that hold none of the bones' carried places (`bone`), the deepest whose peak lies on the knee's
    inner side of the notch (`inner_mm`) and behind the inner condyle's peak (`back_mm`, each
    place's position toward the back). Empty when none does."""
    regions = np.unique(labels[bone & (labels > 0)])
    behind = float(back_mm[condyle.peak_rc])
    for peak in peaks:  # the deepest first
        if np.isin(peak.territory, regions):
            continue
        if inner_mm[peak.peak_rc] > 0 and back_mm[peak.peak_rc] > behind:
            return labels == peak.territory
    return np.zeros(labels.shape, dtype=bool)


def semimembranosus_code(
    leg_through_plane: bool,
    knee: str,
    bone_carried: bool,
    notch: bool,
    slice_found: bool,
    condyle: bool,
    found: bool,
) -> str:
    """Whether the semimembranosus tendon was named on its slice, or why not: each check is one of
    its descriptions."""
    if not leg_through_plane:
        return "abstain_leg_runs_in_the_plane"
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if not bone_carried:
        return "abstain_no_bone_carried"
    if not notch:
        return "abstain_no_middle_sagittal_slice"
    if not slice_found:
        return "abstain_no_tibia_below_the_femur"
    if not condyle:
        return "abstain_no_inner_condyle"
    if not found:
        return "abstain_no_tendon_at_the_back_inner_corner"
    return "identified"


def tibia_top_slice(
    femur_held: list[bool], tibia_held: list[bool], up_mm: list[float]
) -> int | None:
    """The slice through the top of the tibia, just below the joint line: of the slices that hold
    the tibia's carried places and none of the femur's, below every slice that holds the femur's,
    the highest along the leg (`up_mm`, each slice's position toward the head). None when none
    does."""
    lowest_femur = min(
        (up for held, up in zip(femur_held, up_mm, strict=True) if held),
        default=float("inf"),
    )
    below = [
        index
        for index, (femur, tibia, up) in enumerate(
            zip(femur_held, tibia_held, up_mm, strict=True)
        )
        if tibia and not femur and up < lowest_femur
    ]
    return max(below, key=lambda index: up_mm[index]) if below else None


def semimembranosus_on_slice(
    dark: np.ndarray,
    free: np.ndarray,
    region: np.ndarray,
    condyle: Peak,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The semimembranosus tendon at the top of the tibia: the low signal among the places no part
    holds (`free`), its cracks one pixel wide closed (`FOUR_NEIGHBOURS`), and of its pieces at
    least `MENISCUS_THICKNESS_MM` thick, those whose middle lies inside the inner condyle's peak
    (`inner_mm`) and behind it (`back_mm`), the back-inner corner, and that reach within
    `SHELL_MM` of the condyle's `region`; the front one. Empty when none does. `measures` are the
    slice's shared measures, when its caller keeps them: each place's distance from the condyle's
    region is read from them."""
    # The scanner's grain lifts some of the tendon's pixels just above the lens's level, so the
    # lens draws it cracked; a crack one pixel wide is closed before the thin parts are rubbed away.
    body = ndi.binary_closing(dark & free, structure=FOUR_NEIGHBOURS) & free
    pieces, count = ndi.label(thick_parts(body, spacing_rc, MENISCUS_THICKNESS_MM))
    none = np.zeros(dark.shape, dtype=bool)
    if not count:
        return none
    index = np.arange(1, count + 1)
    to_region = (
        distance_from(region, spacing_rc)
        if measures is None
        else measures.distance(region, spacing_rc)
    )
    back = np.asarray(ndi.mean(back_mm, pieces, index=index))
    inner = np.asarray(ndi.mean(inner_mm, pieces, index=index))
    corner = (
        (inner > float(inner_mm[condyle.peak_rc]))
        & (back > float(back_mm[condyle.peak_rc]))
        & (np.asarray(ndi.minimum(to_region, pieces, index=index)) <= SHELL_MM)
    )
    if not corner.any():
        return none
    return pieces == int(index[corner][np.argmin(back[corner])])


def patella_code(
    front_to_back_in_plane: bool,
    femur_named: bool,
    fat_suppressed: bool,
    peak_found: bool,
    found: bool,
) -> str:
    """Whether the patella was named by this slice's own light, or why not.

    Without fat suppression the fat pad under the patella is as bright as marrow, so light cannot
    part them; there the patella is laid on from the fat-suppressed slice of the same place
    (`with_partner`).
    """
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if not femur_named:
        return "abstain_no_femur"
    if not fat_suppressed:
        return "abstain_fat_as_bright_as_marrow"
    if not peak_found:
        return "abstain_no_peak_in_front_of_the_femur"
    if not found:
        return "abstain_nothing_like_the_femur_at_its_peak"
    return "identified"


def patella_peak(
    peaks: tuple[Peak, ...], femur: np.ndarray, basis_lps: np.ndarray
) -> Peak | None:
    """The deepest peak in front of the femur, no higher than `PATELLA_ABOVE_MM` above the femur's
    lowest place: where the patella rides on the femur's lower end. None when there is none.

    Places are read along the patient's axes in the slice's own frame: y toward the back, z up.
    """
    at = np.argwhere(femur).astype(np.float64) @ basis_lps.T
    if not at.size:
        return None
    front, lowest = float(at[:, 1].min()), float(at[:, 2].min())
    for peak in peaks:  # the deepest first
        place = basis_lps @ np.asarray(peak.peak_rc, dtype=np.float64)
        if place[1] < front and lowest <= place[2] <= lowest + PATELLA_ABOVE_MM:
            return peak
    return None


def patella_piece(
    plane: np.ndarray,
    labels: np.ndarray,
    peak: Peak,
    light: float,
    spacing_rc: np.ndarray,
) -> np.ndarray:
    """The patella around its peak: in the peak's territory, the places within `LIKE_THE_FEMUR` of
    the femur's light `light`; of those pieces, the one holding most of the peak's own disc (the
    deepest the lens fits there, so one speckled place at the peak does not lose it); its holes
    filled. Empty when nothing there is as bright as the femur."""
    if light <= 0:
        return np.zeros(plane.shape, dtype=bool)
    low, high = LIKE_THE_FEMUR
    share = plane / light
    like = (labels == peak.territory) & (share >= low) & (share <= high)
    pieces, count = ndi.label(like, structure=FOUR_NEIGHBOURS)
    rows, cols = np.indices(plane.shape)
    r0, c0 = peak.peak_rc
    disc = ((rows - r0) * spacing_rc[0]) ** 2 + (
        (cols - c0) * spacing_rc[1]
    ) ** 2 <= peak.depth_mm**2
    held = np.bincount(pieces[disc & (pieces > 0)], minlength=count + 1)[1:]
    if not held.any():
        return np.zeros(plane.shape, dtype=bool)
    return ndi.binary_fill_holes(pieces == int(np.argmax(held)) + 1)


def fibula_block(
    centres_lps: np.ndarray,
    tibia_top_mm: float,
    tibia_middle_lps: np.ndarray,
    knee: str,
) -> np.ndarray:
    """The squint tiles where the fibula must be: below the tibia's top, on the knee's outer side of
    the tibia's middle. Empty when the header names no knee.

    Positions are the tiles' centres in the scanner's millimetres: x toward the patient's left, y
    toward the back, z up. The outer side is the patient's right for a right knee ("R") and the
    patient's left for a left one ("L").
    """
    if knee not in ("R", "L"):
        return np.zeros(centres_lps.shape[:-1], dtype=bool)
    across = centres_lps[..., 0] - tibia_middle_lps[0]
    outer = across < 0 if knee == "R" else across > 0
    below = centres_lps[..., 2] < tibia_top_mm
    return outer & below


def fibula_on_slice(
    labels: np.ndarray,
    plane: np.ndarray,
    pixel_mm2: float,
    places_lps: np.ndarray,
    tibia_before: np.ndarray,
    tibia_middle_lps: np.ndarray,
    cut: np.ndarray,
) -> tuple[int | None, float]:
    """On one slice's block, the fibula's territory and its area in square millimetres; (None, 0.0)
    when the block holds none.

    The fibula is the bone under the tibia's outer back that looks like the tibia. Of the regions
    the lens draws there, apart from the tibia and at least a disc `BONE_MM` across: those as
    bright as the tibia (within `LIKE_THE_TIBIA`), whose middle lies at least `FIBULA_BELOW_MM`
    below the tibia's top and behind the tibia's middle; the largest of them. The tibia on this
    slice is the region holding most of `tibia_before`, the tibia's places on the middle slice:
    anatomy is contiguous from slice to slice. A region the block's own edge cuts through (`cut`:
    the block's border where it is not the picture's edge) is not a whole object in view, so it is
    not the fibula; the fibula may run off the picture itself. `labels` and `plane` are the block's
    regions and light; `places_lps` (R, C, 3) its places in the scanner's millimetres, y toward
    the back, z up.
    """
    held = labels[tibia_before & (labels > 0)]
    if not held.size:
        return None, 0.0
    tibia_here = int(np.argmax(np.bincount(held)))
    tibia = labels == tibia_here
    light = float(np.median(plane[tibia]))
    top = float(places_lps[tibia][:, 2].max())
    least = np.pi * (BONE_MM / 2.0) ** 2
    low, high = LIKE_THE_TIBIA
    best, area = None, 0.0
    for territory in range(1, int(labels.max()) + 1):
        place = labels == territory
        size = float(np.count_nonzero(place)) * pixel_mm2
        if territory == tibia_here or size < least or size <= area or light <= 0:
            continue
        if (place & cut).any():
            continue
        middle = places_lps[place].mean(axis=0)
        like = low <= float(np.median(plane[place])) / light <= high
        below = top - float(middle[2]) >= FIBULA_BELOW_MM
        behind = float(middle[1]) > float(tibia_middle_lps[1])
        if like and below and behind:
            best, area = territory, size
    return best, area


def main_slice(areas: list[float]) -> int | None:
    """The slice where the object's region is largest; None when no slice holds it."""
    if not any(area > 0 for area in areas):
        return None
    return int(np.argmax(areas))


def fibula_code(knee: str, tibia_named: bool, fat_suppressed: bool, found: bool) -> str:
    """Whether the fibula was named, or why not.

    Marrow is mostly fat, so a fat-suppressed sequence darkens it to the light of muscle; there
    "as bright as the tibia" cannot tell bone from soft tissue, and the fibula is not named.
    """
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if not tibia_named:
        return "abstain_no_tibia"
    if fat_suppressed:
        return "abstain_marrow_suppressed_with_the_fat"
    if not found:
        return "abstain_no_bone_like_the_tibia_below_it"
    return "identified"


def thick_parts(
    mask: np.ndarray, spacing_rc: np.ndarray, thickness_mm: float
) -> np.ndarray:
    """`mask` with every part thinner than `thickness_mm` rubbed away (an opening by a disc)."""
    radius = thickness_mm / 2.0
    half = np.maximum(1, np.floor(radius / spacing_rc)).astype(int)
    rows, cols = np.mgrid[-half[0] : half[0] + 1, -half[1] : half[1] + 1]
    disc = (rows * spacing_rc[0]) ** 2 + (cols * spacing_rc[1]) ** 2 <= radius**2
    return ndi.binary_opening(mask, structure=disc)


def end_pieces(
    pieces: np.ndarray, count: int, across: np.ndarray, middle: float
) -> list[tuple[int, bool]]:
    """The piece nearest each end of the joint: the outermost piece on each side of its middle.

    `across` is each place's position toward the patient's left, and `middle` is the joint's
    middle on it. Each piece comes with whether its end is the one toward the patient's left.
    """
    if not count:
        return []
    labels = np.arange(1, count + 1)
    where = np.asarray(ndi.mean(across, pieces, index=labels))
    chosen = []
    for toward_left, side in ((False, where < middle), (True, where >= middle)):
        if side.any():
            outermost = np.where(side, np.abs(where - middle), -1.0)  # only this side's
            chosen.append((int(labels[int(np.argmax(outermost))]), toward_left))
    return chosen


def between_along_the_leg(
    upper: np.ndarray, lower: np.ndarray, basis_lps: np.ndarray
) -> np.ndarray:
    """The places between `upper` and `lower` on each line along the leg, where both lie on it.

    The line is the pixel axis nearer the leg's axis; on it, the places after the last `upper`
    place and before the first `lower` place.
    """
    rows_axis = abs(basis_lps[2, 0]) >= abs(basis_lps[2, 1])
    a, b = (upper, lower) if rows_axis else (upper.T, lower.T)
    superior_step = basis_lps[2, 0] if rows_axis else basis_lps[2, 1]
    if superior_step > 0:  # superior lies toward larger indices: walk the other way
        a, b = a[::-1], b[::-1]
    index = np.arange(a.shape[0])[:, None]
    last_upper = np.where(a, index, -1).max(axis=0, initial=-1)
    first_lower = np.where(b, index, a.shape[0]).min(axis=0, initial=a.shape[0])
    both = (last_upper >= 0) & (first_lower < a.shape[0]) & (last_upper < first_lower)
    between = both & (index > last_upper) & (index < first_lower)
    if superior_step > 0:
        between = between[::-1]
    return between if rows_axis else between.T


@dataclass(frozen=True, slots=True)
class Field:
    """A slice's field, read before any part is named and shared by every rule on the slice: the
    leg (every territory the lens draws, its holes filled), the air outside it and the skin that
    touches the air, named in `objects` with their codes, each territory's strongest interior peak
    (the deepest first), and which of the patient's axes lie in the slice's plane (side to side,
    front to back, along the leg). A part named on a slice of its own reads only this."""

    leg: np.ndarray
    objects: np.ndarray
    codes: dict[str, str]
    peaks: tuple[Peak, ...]
    in_plane: tuple[bool, bool, bool]


def read_field(
    plane: np.ndarray,
    reading: InteriorReading,
    basis_lps: np.ndarray,
    outside_picture: np.ndarray | None = None,
) -> Field:
    """One slice's field (`Field`): AIR, the low signal outside the leg and its black margin where
    it forms a field (`fields`), and SKIN, the leg's places touching the air (their paragraphs in
    the module note); the territories' peaks; and which way the slice faces. `outside_picture` is
    the slice's black margin (`margin`), when the caller has found it already."""
    dark, labels = reading.dark, reading.labels
    outside_picture = margin(plane) if outside_picture is None else outside_picture
    objects = np.zeros(plane.shape, dtype=np.int8)
    codes: dict[str, str] = {}
    leg = ndi.binary_fill_holes(labels > 0)
    spacing_rc = np.linalg.norm(basis_lps, axis=0)
    air = fields(dark & ~leg & ~outside_picture, spacing_rc) & leg.any()
    objects[air] = OBJECT_CODES["air"]
    codes["air"] = (
        "identified"
        if air.any()
        else "abstain_no_leg"
        if not leg.any()
        else "abstain_no_field_outside_the_leg"
    )
    skin = leg & ndi.binary_dilation(air, structure=FOUR_NEIGHBOURS)
    objects[skin] = OBJECT_CODES["skin"]
    codes["skin"] = "identified" if skin.any() else "abstain_no_air"
    peaks = territory_peaks(labels, reading.distance_mm, basis_lps)
    # frozen: every stage that reads the slice is handed the same arrays; one that names a part
    # on them names it on a copy
    return Field(
        handed_on(leg), handed_on(objects), codes, peaks, axes_in_plane(basis_lps)
    )


def assign_plane(
    plane: np.ndarray,
    reading: InteriorReading,
    basis_lps: np.ndarray,
    knee: str = "",
    fat_suppressed: bool = False,
    fluid_sensitive: bool = False,
    outside_picture: np.ndarray | None = None,
    field: Field | None = None,
    measures: Measures | None = None,
) -> PlaneAssignment:
    """Name air, skin, femur, tibia, joint, patella, menisci, cartilage, the PCL, the MCL, the
    joint's fluid, Hoffa's fat pad, the suprapatellar fat and the fat under the skin on one plane,
    from its interiors; and keep the dark bands the PCL is read from, for the extensor tendons, the
    white the joint's fluid is named from, for muscle on the slice of the same place, and which of
    the patient's axes lie in the slice's plane.

    `knee` is the header's own word for which knee the scan is, "R", "L" or blank; it sides the
    menisci. `fat_suppressed` and `fluid_sensitive` are the series' own tags; only with fat
    suppression is the patella named by its light, and only with both is the fluid white.
    `outside_picture` is the slice's black margin (`margin`) and `field` its field (`read_field`:
    the leg, the air and the skin, the peaks, which way it faces), when the caller has read them
    already. `measures` are the slice's shared measures (`Measures`): the marrow's light, each
    place's distance from a part, its position along the patient's axes, each read once on the
    slice and handed to every rule that asks; without them each rule reads its own.
    """
    dark, labels = reading.dark, reading.labels
    outside_picture = margin(plane) if outside_picture is None else outside_picture
    field = (
        read_field(plane, reading, basis_lps, outside_picture)
        if field is None
        else field
    )
    objects = field.objects.copy()
    codes = dict(field.codes)
    leg, peaks, in_plane = field.leg, field.peaks, field.in_plane
    sides_in_plane, front_in_plane, leg_in_plane = in_plane
    spacing_rc = np.linalg.norm(basis_lps, axis=0)
    air = objects == OBJECT_CODES["air"]
    skin = objects == OBJECT_CODES["skin"]

    # FEMUR and TIBIA: the deepest territory, and the deepest one above or below it.
    partner = None
    if leg_in_plane and peaks:
        partner = next(
            (
                peak
                for peak in peaks[1:]
                if along_the_leg(basis_lps, peaks[0].peak_rc, peak.peak_rc)
                >= ALONG_THE_LEG
            ),
            None,
        )
    codes["femur"] = codes["tibia"] = codes["joint"] = pair_code(
        leg_in_plane, len(peaks), partner is not None
    )
    femur = tibia = None
    if partner is not None:
        upper, lower = sorted(
            (peaks[0], partner), key=lambda peak: peak.superior_mm, reverse=True
        )
        femur, tibia = upper.territory, lower.territory
        objects[labels == femur] = OBJECT_CODES["femur"]
        objects[labels == tibia] = OBJECT_CODES["tibia"]
        # JOINT: what lies between the two bones along the leg.
        joint = (
            between_along_the_leg(labels == femur, labels == tibia, basis_lps)
            & (objects == 0)
            & ~outside_picture
        )
        objects[joint] = OBJECT_CODES["joint"]
        codes["joint"] = "identified" if joint.any() else "abstain_nothing_between"

    # PATELLA: on a fat-suppressed sagittal slice, the bone as bright as the femur at the deepest
    # peak in front of the femur's lower end.
    femur_places = objects == OBJECT_CODES["femur"]
    peak = (
        patella_peak(peaks, femur_places, basis_lps)
        if front_in_plane and femur is not None
        else None
    )
    piece = np.zeros(plane.shape, dtype=bool)
    if peak is not None and fat_suppressed:
        light = (
            marrow_light(plane, femur_places)
            if measures is None
            else measures.light(femur_places)
        )
        piece = patella_piece(plane, labels, peak, light, spacing_rc) & (objects == 0)
    codes["patella"] = patella_code(
        front_in_plane,
        femur is not None,
        fat_suppressed,
        peak is not None,
        bool(piece.any()),
    )
    patella = None
    if peak is not None and codes["patella"] == "identified":
        objects[piece] = OBJECT_CODES["patella"]
        patella = peak.territory

    # MENISCI: the thick low signal touching the joint, whole, the piece nearest each end.
    menisci = 0
    joint_places = objects == OBJECT_CODES["joint"]
    if sides_in_plane and joint_places.any():
        thick = thick_parts(dark & ~outside_picture, spacing_rc, MENISCUS_THICKNESS_MM)
        pieces, _ = ndi.label(thick)
        near_joint = ndi.binary_dilation(joint_places, structure=FOUR_NEIGHBOURS)
        touching = np.unique(pieces[near_joint & (pieces > 0)])
        pieces = np.where(np.isin(pieces, touching), pieces, 0)
        pieces, count = ndi.label(pieces > 0)
        leftward = (
            positions_along(plane.shape, basis_lps, 0)
            if measures is None
            else measures.along(0)
        )
        middle = float(leftward[joint_places].mean())  # the joint's middle
        for piece, toward_left in end_pieces(pieces, count, leftward, middle):
            side = meniscus_side(knee, toward_left)
            name = "meniscus" if side == "meniscus" else f"{side}_meniscus"
            objects[pieces == piece] = OBJECT_CODES[name]
            menisci += 1
    codes["meniscus"] = meniscus_code(sides_in_plane, joint_places.any(), menisci)
    codes["meniscus_side"] = side_code(knee, menisci)

    # ARTICULAR CARTILAGE: on a fat-suppressed coronal slice, the bright layer on each bone, in the
    # joint.
    joint_named = codes["joint"] == "identified"
    femoral = tibial = np.zeros(plane.shape, dtype=bool)
    if sides_in_plane and fat_suppressed and joint_named:
        femoral, tibial = cartilage_on(plane, objects, spacing_rc, measures)
    codes["cartilage"] = cartilage_code(
        sides_in_plane, fat_suppressed, joint_named, bool(femoral.any() or tibial.any())
    )
    objects[femoral] = OBJECT_CODES["femoral_cartilage"]
    objects[tibial] = OBJECT_CODES["tibial_cartilage"]

    # PCL: on a sagittal slice without fat suppression, the thick, uniformly dark band joining the
    # femur and the tibia. The slice's dark bands are kept: the extensor tendons are another of
    # them, named once the patella is laid on from the fat-suppressed slice of the same place.
    bones_named = femur is not None and tibia is not None
    pcl = np.zeros(plane.shape, dtype=bool)
    bands = None
    if front_in_plane and not fat_suppressed and bones_named:
        bands = dark_bands(plane, objects, spacing_rc, outside_picture, measures)
        pcl = band_joining(
            bands,
            objects == OBJECT_CODES["femur"],
            objects == OBJECT_CODES["tibia"],
            spacing_rc,
            measures,
        )
        pcl &= np.isin(objects, (0, OBJECT_CODES["joint"]))
    codes["pcl"] = pcl_code(
        front_in_plane, fat_suppressed, bones_named, bool(pcl.any())
    )
    objects[pcl] = OBJECT_CODES["pcl"]
    # PATELLAR and QUADRICEPS TENDONS: named from those bands with the partner's patella
    # (`extensor_tendons`); read alone, a slice says only why it cannot.
    for name, above in (("patellar_tendon", False), ("quadriceps_tendon", True)):
        codes[name] = tendon_code(front_in_plane, fat_suppressed, False, False, above)

    # MCL: on a coronal slice, the low signal left on the medial meniscus's side that joins the
    # femur and the tibia.
    medial = bool((objects == OBJECT_CODES["medial_meniscus"]).any())
    mcl = np.zeros(plane.shape, dtype=bool)
    if sides_in_plane and medial:
        mcl = ligament_on_the_inner_side(
            dark, objects, basis_lps, outside_picture, measures
        )
    codes["mcl"] = mcl_code(sides_in_plane, medial, bool(mcl.any()))
    objects[mcl] = OBJECT_CODES["mcl"]

    # JOINT FLUID: with fat suppression on a fluid-sensitive sequence, the white in the joint's
    # recesses. The white is kept, for the muscle of the slice of the same place without it.
    fluid_bright = fat_suppressed and fluid_sensitive
    white = (
        white_as_fluid(plane, objects, measures)
        if fluid_bright and bones_named
        else None
    )
    fluid = np.zeros(plane.shape, dtype=bool)
    if white is not None:
        fluid = fluid_in_the_recesses(
            white, objects, leg, outside_picture, spacing_rc, measures
        )
    codes["joint_fluid"] = fluid_code(fluid_bright, bones_named, bool(fluid.any()))
    objects[fluid] = OBJECT_CODES["joint_fluid"]

    # HOFFA'S FAT PAD and the SUPRAPATELLAR FAT: with fat suppression, the rest of the patella's
    # territory below it and above it.
    patella_places = objects == OBJECT_CODES["patella"]
    for name, upward in (("hoffa_fat_pad", False), ("suprapatellar_fat", True)):
        pad = np.zeros(plane.shape, dtype=bool)
        if front_in_plane and fat_suppressed and patella is not None:
            pad = rest_of_the_patellas_territory(
                labels, patella, patella_places, objects, basis_lps, upward, measures
            )
        codes[name] = fat_pad_code(
            front_in_plane, fat_suppressed, patella is not None, bool(pad.any()), upward
        )
        objects[pad] = OBJECT_CODES[name]

    # FAT UNDER THE SKIN: without fat suppression, the places as bright as marrow outside every
    # part named, in the pieces reaching the skin; last, since it is what lies outside the rest.
    fat = np.zeros(plane.shape, dtype=bool)
    if not fat_suppressed and skin.any() and femur is not None:
        fat = fat_under_the_skin(plane, objects, spacing_rc, measures)
    codes["subcutaneous_fat"] = subcutaneous_code(
        fat_suppressed, bool(skin.any()), femur is not None, bool(fat.any())
    )
    objects[fat] = OBJECT_CODES["subcutaneous_fat"]

    # MUSCLE: named once the slice is read with its partner, outside the white that partner sees as
    # fluid where it is fat-suppressed and fluid-sensitive (`muscle_bodies`); read alone, a slice
    # keeps muscle's code as not named, and with fat suppression says why.
    codes["muscle"] = muscle_code(
        fat_suppressed, bool(air.any()), femur is not None, False
    )
    # Located after the sequences have supplied their named parts; these surfaces overlap fluid.
    codes["anterior_synovial_recess"] = codes["synovium"] = "not_named_on_this_slice"
    return PlaneAssignment(
        objects, codes, peaks, femur, tibia, patella, bands, white, in_plane
    )


def places_from(
    seen: np.ndarray,
    frame: PlaneFrame,
    onto: PlaneFrame,
    onto_shape: tuple[int, int],
    thickness_mm: float,
) -> np.ndarray | None:
    """For each place of another slice of the same knee, the flat index of this slice's nearest
    pixel, and -1 where the place lies outside this slice's picture: beyond its edge, or where
    `seen` is False (its black margin, which the reconstruction never filled), so this slice has no
    say there. None when the other slice is not the same place (some place of it lies more than
    half a slice thickness off this slice's plane). The match is made once for a pair of slices and
    lays any of this slice's readings onto the other (`laid_by`). `frame` is this slice's and
    `onto` the other's, in the scanner's millimetres (DICOM LPS): the other's places are put in
    them (`PlaneFrame.to_patient`) and carried onto this one (`PlaneFrame.normal`,
    `PlaneFrame.to_native`).
    """
    rows, cols = np.indices(onto_shape)
    places = onto.to_patient(
        np.column_stack((rows.ravel(), cols.ravel())).astype(np.float64)
    )
    if float(np.abs((places - frame.origin_lps) @ frame.normal()).max()) > (
        thickness_mm / 2.0
    ):
        return None
    native = np.rint(frame.to_native(places)).astype(int)
    inside = (
        (native[:, 0] >= 0)
        & (native[:, 0] < seen.shape[0])
        & (native[:, 1] >= 0)
        & (native[:, 1] < seen.shape[1])
    )
    inside[inside] = seen[native[inside, 0], native[inside, 1]]
    source = np.full(rows.size, -1, dtype=np.int64)
    source[inside] = native[inside, 0] * seen.shape[1] + native[inside, 1]
    return source.reshape(onto_shape)


def laid_by(values: np.ndarray, source: np.ndarray) -> np.ndarray:
    """One slice's `values` at the places of another slice of the same knee, by their match
    (`source`, from `places_from`), and `UNSEEN` where this slice has no say."""
    laid = np.full(source.shape, UNSEEN, dtype=values.dtype)
    seen = source >= 0
    laid[seen] = values.ravel()[source[seen]]
    return laid


def with_partner(
    assignment: PlaneAssignment,
    labels: np.ndarray,
    basis_lps: np.ndarray,
    outside_picture: np.ndarray,
    laid: np.ndarray,
    partner_codes: dict[str, str],
) -> tuple[np.ndarray, dict[str, str]]:
    """One slice's named objects and codes, read with its partner's: the other sequence's slice of
    the same place (`laid`, the partner's objects at this slice's places, from `laid_by`).

    A bone both name is named where both agree, and where the partner's picture does not reach
    (`UNSEEN`: it has no say there); not at all where they share no place. A part only the partner
    names (the patella, the menisci, the cartilage, the PCL, the MCL, the joint's fluid, Hoffa's fat
    pad, the suprapatellar fat, and last the air and the skin) is laid on from it, onto this
    slice's own interiors that nothing else holds; the patella only where it holds this slice's own
    peak in front of the femur, so the two lenses agree on where it is. The joint is then again
    what lies between the bones along the leg.
    """
    objects, codes = assignment.objects.copy(), dict(assignment.codes)
    for name in BONES:
        code = OBJECT_CODES[name]
        own, theirs = objects == code, laid == code
        if codes.get(name) in NAMED and partner_codes.get(name) in NAMED:
            agreed = own & (theirs | (laid == UNSEEN))
            objects[own & ~agreed] = 0
            codes[name] = (
                "agreed_with_its_partner"
                if agreed.any()
                else "abstain_the_two_slices_disagree"
            )
        elif partner_codes.get(name) in NAMED:
            placed = theirs & (labels > 0) & (objects == 0)
            objects[placed] = code
            if placed.any():
                codes[name] = "laid_from_its_partner"
    joint = OBJECT_CODES["joint"]
    objects[objects == joint] = 0
    femur, tibia = objects == OBJECT_CODES["femur"], objects == OBJECT_CODES["tibia"]
    between = np.zeros(objects.shape, dtype=bool)
    if femur.any() and tibia.any():
        between = between_along_the_leg(femur, tibia, basis_lps)
        between &= (objects == 0) & ~outside_picture
    objects[between] = joint
    if codes.get("joint") in NAMED or between.any():
        codes["joint"] = "identified" if between.any() else "abstain_nothing_between"
    for name, members in (
        ("patella", ("patella",)),
        ("meniscus", MENISCI),
        ("cartilage", CARTILAGES),
        ("pcl", ("pcl",)),
        ("mcl", ("mcl",)),
        ("joint_fluid", ("joint_fluid",)),
        ("hoffa_fat_pad", ("hoffa_fat_pad",)),
        ("suprapatellar_fat", ("suprapatellar_fat",)),
        # last, so they take no place another laid part would
        ("air", ("air",)),
        ("skin", ("skin",)),
    ):
        if codes.get(name) in NAMED or partner_codes.get(name) not in NAMED:
            continue
        theirs = np.isin(laid, [OBJECT_CODES[member] for member in members])
        if name == "patella":
            peak = patella_peak(assignment.peaks, femur, basis_lps)
            if peak is None or not theirs[peak.peak_rc]:
                codes[name] = "abstain_the_two_slices_disagree"
                continue
        placed = theirs & (labels > 0) & np.isin(objects, (0, joint))
        objects[placed] = laid[placed]
        if placed.any():
            codes[name] = "laid_from_its_partner"
            if name == "meniscus":
                codes["meniscus_side"] = partner_codes.get("meniscus_side", "")
    return objects, codes
