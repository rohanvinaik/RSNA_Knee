"""Name the objects that are plain in the interiors' pictures, one at a time.

Each is an «<object>» (Rohan, 2026-10-14): a set of descriptions of how it appears in these scans,
read off the interiors' own lenses, each one check with the code it abstains with, and the
categories of the twelve it relates to (docs/OBJECTS_AND_CONDITIONS.md §6):

- ILIOTIBIAL BAND (ITB): «a distal continuation of the deep fascia lata of the thigh which inserts
  onto Gerdy's tubercle on the anterolateral proximal tibia», «seen as a broad, thick band of low
  signal extending from the anterolateral thigh», in front of the LCL and the biceps tendon (Chien
  et al. 2020, PDF pp. 14-15, Figure 29). Seen on the proof's non-fat-suppressed coronals,
  2026-10-16 (raw, at native pixels, slices 6 to 15): outside the femur's lateral condyle the bright
  subcutaneous fat lies in a vertical band, and directly on its deep surface runs one thin dark
  line, about 0 to 130 against the fat's 400 to 700 and the muscle's 250 to 450, from the top of the
  picture down past the joint to the tibia's top-lateral corner; below that it goes on as the
  crural fascia. It is named on the existing middle coronal (a standard first slice) by these
  descriptions, each one check with its code (`itb_code`, `iliotibial_band`):
  1. side to side and the leg both lie in the slice's plane, as on a coronal slice
     (abstain_side_to_side_runs_through_the_plane; abstain_leg_runs_through_the_plane);
  2. the header names the knee, so its outer side is known (abstain_header_names_no_knee);
  3. fat is not suppressed: the layer is the subcutaneous fat the sequences without suppression
     name; on the fat-suppressed twin the ITB is laid on (abstain_not_parted_from_the_fat_with_fat_suppression);
  4. the slice names the femur, the tibia and the subcutaneous fat (abstain_no_femur_and_tibia;
     abstain_no_subcutaneous_fat); on each native cross-section across the leg (the sections are
     indexed along the native axis the leg runs along) the layer is that fat lying outboard of the
     bones (abstain_no_fat_outside_the_bones);
  5. the line is the lowest acquired signal in the strip deeper than the layer's deep edge by at
     most `SHELL_MM`, kept whole when its tied minimum is one contiguous run and darker than the
     median light of the layer and of the next `SHELL_MM` beyond the strip, the deep neighbour: a dip
     between two lighter tissues, not a slope from fat to muscle. `SHELL_MM` is the 2 mm reach
     every rule here allows a thin dark band to its neighbour; no signal cutoff is added, nothing
     is smoothed, and no section is read from its neighbours (abstain_no_dark_line_deep_to_the_fat);
  6. the band is kept from the picture's top down to the most superior section where a line comes
     within `SHELL_MM` of the tibia, its insertion (abstain_band_does_not_reach_the_tibia), and
     passes a section holding the femur (abstain_band_not_beside_the_femur).
  This localizes the band's course as a trace: it does not measure thickness or the exact insertion
  on Gerdy's tubercle, and leaves out the sections whose line is not a clean dip (on the proof 48
  of 384 sections are not darker than both sides, 8 have two separated tied minima). It names the
  deep fascia where it lies against the subcutaneous fat, so a band deeper than the fat would not
  be reached, and the slice law is the middle coronal's, not a search for the band's best slice.
  The layer, strip, candidate lines and per-section light are retained as readings. It relates to
  none of the twelve conditions directly: it is the outer neighbour of the lateral complex the LCL
  belongs to.

- POPLITEUS TENDON: the structure in the lateral femoral sulcus, localized on the coronal slice
  through the fibular attachment already selected for the LCL. It is named on the
  non-fat-suppressed slice and laid onto its twin by the existing physical-place match. Its
  descriptions, each one check with its code:
  1. the LCL-selected slice is the reference (abstain_requires_the_lcl_slice);
  2. carry the femur from the same series' middle slice into the saved lens regions, and retain the
     existing LCL region as a relational target only (abstain_no_femoral_region;
     abstain_no_lcl_region);
  3. measure the carried femur's pixel-centre convex envelope (`convex_envelope`; measured,
     abstain_fewer_than_three_points, abstain_no_area), then name the largest four-connected part
     of the LCL region inside that envelope and outside the femur (`popliteus_in_notch`;
     abstain_no_lateral_femoral_notch).
  This localizes the tendon in the sulcus on this slice, may include a cortex rim or partial
  cross-section, and does not claim its full course. It relates to none of the twelve conditions
  directly.

- BICEPS FEMORIS TENDON (proximal): the dark cord that joins the posterior thigh muscle to the
  fibular head, part of the lateral complex with the LCL and the iliotibial band
  (docs/OBJECTS_AND_CONDITIONS.md; Chien et al. 2020, where it lies behind the ITB and beside the
  LCL). Seen on the proof's fat-bright sagittals, 2026-10-16 (the inspected prototype picture): on
  the slice just beyond the fibular head's lateral face, a long dark body runs from the lower end
  of the posterior thigh muscle down to the head's marrow; the LCL, which also reaches the head,
  lies on the slices medial to it. It is named on a slice of its own by these descriptions, each
  one check with its code (`lateral_to_the_head`, `proximal_biceps_on_slice`):
  1. its slice: from the fibula's main slice, the fibula's places are carried along the series
     normal as a projection, not a slab (`projected_places`), and the walk goes toward the knee's
     outer side while the marrow-like body holding them (`fibula_like_head`) is still at least a
     disc `BONE_DISC_MM2` (a disc `BONE_MM` across); the answer is the first slice outward where it
     is not. Read lazily, slice by slice, with no scan of the series: a slice the walk never read
     keeps NaN, not 0, since "cannot say" is not "measured empty" (`HEAD_SLICE_STATUS`)
     (abstain_header_names_no_knee; abstain_no_fibula; abstain_slices_do_not_run_side_to_side;
     abstain_the_series_has_one_slice; abstain_no_slice_thickness;
     abstain_no_slice_holds_the_fibula; abstain_head_unreadable_on_the_way;
     abstain_the_fibula_is_not_a_disc_on_its_main_slice;
     abstain_the_series_ends_before_the_head_does);
  2. the head's body on a slice is the region as bright as the fibula's own marrow (within
     `LIKE_THE_TIBIA` of its light) that holds most of the projected fibula's places, after
     specks and bridges narrower than three native pixels are taken out by one erosion and
     dilation with a 3 x 3 square (a sampling-scale operation: its reach in millimetres is the
     pixel pitch, not an anatomical 3 mm; being an opening it closes no crack and fills no hole);
     no projected fibula, no body, or two bodies holding exactly as many places give no head
     (abstain_no_fibula_marrow_light; abstain_no_projected_fibula;
     abstain_no_marrow_like_body_at_the_fibula; abstain_tied_head_bodies);
  3. the slice is a sagittal one without fat suppression, where the head's marrow is bright and the
     cord dark, with its fat-suppressed twin laid on the same pixels, and the fibula's marrow
     light in both acquisitions is known and positive (abstain_empty_slice;
     abstain_marrow_as_dark_as_a_ligament_with_fat_suppression;
     abstain_front_to_back_runs_through_the_plane; abstain_leg_runs_through_the_plane;
     abstain_no_fibula_marrow_light; abstain_no_suppressed_marrow_light;
     abstain_no_twin_on_the_slice; abstain_no_fibular_head_on_the_slice);
  4. the cord is dark in both acquisitions, each read as a median along the leg over
     `LIGAMENT_THICK_MM`, and a place the filter cannot fully see (outside the twin's picture, or
     not finite) has no reading at all, never a zero that would read as dark: without fat
     suppression no brighter than `LIGAMENT_DARKER` of the head's marrow (muscle is as dark, so
     this alone is not it); with it no brighter than the head's own suppressed marrow, which
     muscle, about twice as bright there, is not;
  5. it lies between a muscle and the head along the leg: below the lower end of the muscle belly
     and above the head's top. The belly is the largest body above the head, at least `BONE_MM`
     across, dark without suppression and, suppressed, brighter than the marrow-like band and
     under `FLUID_BRIGHTER` times the head's suppressed marrow; two exactly equal largest bodies
     abstain (abstain_no_muscle_belly_above_the_head; abstain_tied_muscle_bellies);
  6. cortex surrounds marrow: nothing within `SHELL_MM` of a marrow-like body (a thick body at
     least `LIKE_THE_TIBIA`'s lower bound of the head's light, or the head) is taken
     (abstain_nothing_dark_between_the_muscle_and_the_head);
  7. a competent piece: a part at least `LIGAMENT_THICK_MM` thick, at least a disc
     `BONE_DISC_MM2` in area, reaching within `BONE_MM` of both the belly and the head; the
     largest, an exact tie abstaining. Every piece's area, reaches and length are kept, the
     competent ones flagged (abstain_no_competent_piece_joins_the_muscle_and_the_head;
     abstain_tied_competent_pieces).
  What the baseline constants do here. Marrow contrast separates the tissues, never one lens
  alone: `LIKE_THE_TIBIA` says what is the marrow's tissue, `LIGAMENT_DARKER` what is darker than
  marrow and so tendon or muscle, `FLUID_BRIGHTER` the top of the muscle band in the twin. The
  physical body scale separates a belly or a core from a thin seam: `BONE_MM` for the belly, the
  head and the piece's area, `LIGAMENT_THICK_MM` for the cord's thickness and the filter's length.
  `SHELL_MM` and the reach of `BONE_MM` are allowances for broad targets (a marrow body's cortex,
  the belly's and the head's loose ends), not measurements of thickness or of an attachment.
  Limitations, stated and not chased: it is a localization at one validity demonstration, not
  precision or generalization. The head's area on the slice that is chosen lies close to the
  `BONE_MM` disc's boundary, so the slice choice is a proxy for "just beyond the head's lateral
  face" and flips with a pixel or two (no threshold has been tuned to it). The piece may take in
  the LCL's neighbourhood and the arm of the muscle in front, since the dark cord and its
  neighbours are one dark body in these scans, and it leaves any part of the cord that lies
  within `SHELL_MM` of a bright body or on another slice. A thick bright body near the cord (fat)
  counts as marrow and removes its surroundings. It relates to none of the twelve conditions
  directly: the lateral complex's tendon, no label names it.

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
  AX native cross-sections provide a separate reading on the axial acquisition. The coronal
  native, resolved MCL support is projected only as a location target into its half-slab; every
  positive four-connected enclosed-dark component within `SHELL_MM` is retained with its physical
  distance, size and crop-edge status. A whole contacted component is excluded only where an
  independently resolved native femur or tibia support on that same acquisition and slice
  intersects it; unknown bone context stays neutral. Of the remaining contacted components the
  uniquely largest is the body. No opening, signal cutoff, clipping against bone, or claim of a
  full course is made. A selected body with a wholly observed boundary is identified even if another part of the
  crop is unavailable; cut or unavailable-boundary bodies remain readings. Ties and known bone
  conflicts are named. Posteromedial capsule may be included in this local band; its posterior
  overreach is retained without a full-course or insertion claim. This is an axial localization
  with the coronal support as a place to ask, not a second coronal rule.
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
- JOINT CAPSULE: the sleeve around the joint, here the dark wall outside its side recesses.
  Descriptions (capsule_code): a coronal slice (abstain_not_a_coronal_slice); fluid bright with
  fat suppression and fluid sensitivity (abstain_fluid_not_bright_on_this_sequence); a named
  femur (abstain_no_femur); both named menisci locating the joint's ends
  (abstain_no_two_menisci_to_locate_the_side_recesses); and a dark outer wall bordering the
  largest white recess beside the femur outboard of either meniscus
  (abstain_no_dark_outer_wall_at_the_recesses). Only low signal on the side away from the
  femur, over the recess's height, within the existing 2 mm shell/contact allowance is returned.
  This allowance tests contact, not capsule thickness. The mask is kept independently because
  the capsule and the deep collateral structures can share a place. On the proof the outer wall
  of the image-left recess is plain; other stretches are not required for this demonstration.
  The wall relates to Effusion, Synovitis and Baker's as their compartment's boundary.
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
  above it, and a thin strip under the skin along the back of the leg.
- LATERAL GASTROCNEMIUS HEAD: the same body on the knee's outer side, behind the outer
  condyle. It uses the medial head's descriptions and the same `inner_condyle` and
  `gastrocnemius_head` operations with the physical inner-axis negated. The carried bones,
  notch, labels and peaks are shared by both heads. Its two side-specific refusals are
  abstain_no_outer_condyle and abstain_no_body_behind_the_outer_condyle; the other
  `gastrocnemius_code` refusals are unchanged. It is placed only where no object is named.
- POPLITEAL ARTERY AND VEIN: the closed tube cross-sections behind the femoral notch, between
  the two gastrocnemius heads. `enclosed_darkness` raises each dark closed interior from its
  recorded image-border values by erosion reconstruction and subtracts the acquired light; no
  grey-level cutoff is used. `popliteal_lumens` labels every positive interior with 8-neighbour
  connectivity, then considers only complete components inside the corridor between the two head
  peaks, behind both condyle peaks and in front of the heads' posterior extent. A component must
  be touched by `thick_parts` at `VESSEL_BODY_MM` (2 mm), the same physical body-versus-thin-seam
  scale used for other small anatomical bodies; this is not a vessel diameter or wall estimate.
  Of those components, the two with greatest mean enclosed darkness are retained whole. Their
  mean posterior positions order the anterior one as the artery and the posterior one as the vein.
  Fewer than two eligible components abstain as `abstain_no_lumen_pair`; equal posterior means
  abstain as `abstain_ambiguous_vessel_order`. This names lumen cross-sections only, with no claim
  about vessel walls or continuity.
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
- QUADRICEPS AND PREFEMORAL FAT PADS: the anterior wedge behind the quadriceps tendon and
  the posterior strip against the femur, separated by the suprapatellar recess. Descriptions:
  1. the source is sagittal (abstain_not_a_sagittal_slice) and fluid-sensitive with fat suppressed
     (abstain_requires_fluid_sensitive_fat_suppression);
  2. the combined suprapatellar fat is already named (abstain_no_suprapatellar_fat);
  3. a non-fat-suppressed twin images the same place (abstain_no_non_fat_suppressed_twin;
     abstain_no_slice_thickness; abstain_not_the_same_place). Its acquired light is carried by
     the pair's one existing physical match;
  4. on each cross-section along the leg, the internal seam is the greatest relative FS/non-FS
     signal inside the combined fat, with fat on both sides. Flat sections and separated tied
     maxima abstain locally; contiguous ties retain the whole band. No section is interpolated
     (abstain_no_internal_seam when none speaks);
  5. the named fat anterior to that seam is the quadriceps pad; posterior is the prefemoral pad.
  The ratio is an objective reading (`relative_signal`), not a tissue name, and no new numerical
  cutoff is used. Both masks and the seam are retained separately, then laid onto the twin. The
  source retains the aligned light and ratio too. On the proof the two main shapes are separated;
  the seam can deviate near its ends, and the inherited combined field can take in neighbouring
  tissue. This is a partition on the selected slice, not membrane thickness or a full extent.
  The two pads border the recess involved in Effusion; neither has a direct competition label.
- SEMITENDINOSUS TENDON: the separate dark oval behind the semimembranosus tendon on its
  tibial-top axial slice (the shared slice's prerequisites are those of semimembranosus above).
  Its descriptions, checked by `semitendinosus_on_slice`:
  1. the semimembranosus reference is named (abstain_no_semimembranosus_reference);
  2. the inner condyle's peak is known (abstain_no_inner_condyle_peak);
  3. the slice's shared dark-body reading holds candidates (abstain_no_dark_body_candidates).
     The crack closure, small-body scale, labels and mean patient positions are made once by
     `dark_tendon_bodies` and handed to both tendon selectors; there is no fallback construction;
  4. a body's mean lies inside the inner condyle's peak and behind the semimembranosus body's
     posterior extent (abstain_no_body_meets_both_spatial_relations);
  5. of those bodies it is the one nearest the named tendon in physical distance, retained whole;
     an exact tie abstains (abstain_tied_nearest_bodies).
  A separate mask preserves the existing names. On the proof's axial slice 11 the smaller oval
  behind the semimembranosus is selected; no proof position, label or new cutoff enters the rule.
  If the dark bodies join, this definition cannot separate them. This is a cross-section, not a
  claim about the tendon's whole course. None of the twelve categories names it directly.
- GRACILIS TENDON: the thin dark cord on the knee's inner side, on the semimembranosus tendon's
  tibial-top axial slice. The gracilis, with the sartorius and the semitendinosus, attaches on the
  anteromedial tibia, so it lies further forward and further to the inner side than the two
  hamstring tendons behind it (LaPrade et al. 2007, the medial knee; docs/OBJECTS_AND_CONDITIONS.md).
  Seen on the inspected prototype picture, 2026-10-16 (the proof's axial slice, raw at native
  pixels): beside the semimembranosus's and the semitendinosus's black ovals, toward the inner
  skin and in front of the semitendinosus, a separate, thinner dark cord, a few pixels across,
  with bright fat and vessels round it. The shared body reading (`dark_tendon_bodies`) closes
  one-pixel cracks with a 4-neighbour structure and rubs away every part thinner than
  `MENISCUS_THICKNESS_MM` (a disc 4 pixels across at this pitch), which removes this cord. So
  it is read by a complementary sampling lens, `native_dark_bodies`, at the pixel scale: the
  same low signal outside the air, skin and black margin, closed by the 3 x 3 square (8
  neighbours) and opened by the 4-neighbour cross, which rubs away the parts too thin to hold
  the cross (under three pixels across) and trims a kept body's corners.
  Both are sampling-scale operations, not anatomical sizes or signal levels; the shared lens
  and the two named tendons are left as they are. Its descriptions, checked by
  `gracilis_on_slice`, each one check with its code:
  1. the header names the knee, so its inner side is known (abstain_header_names_no_knee);
  2. the semimembranosus and the semitendinosus are both named, the two references
     (abstain_no_semimembranosus_reference; abstain_no_semitendinosus_reference);
  3. the native lens holds dark bodies (abstain_no_native_dark_body);
  4. a candidate is a whole body that overlaps neither named tendon, whose mean lies on the
     inner side of both tendons' means and in front of the semitendinosus's mean
     (abstain_no_body_medial_to_both_and_in_front_of_the_semitendinosus);
  5. of those it is the one nearest the pair of tendons in physical distance, retained whole,
     the distance read from the slice's shared measures; an exact tie abstains
     (abstain_tied_nearest_bodies).
  The labels, each body's mean inner and back positions, the eligible bodies and their
  distances are all retained as readings. No proof coordinate, component number or signal
  cutoff enters the rule, and no ratio or window from any other part. If the cord is joined to
  another dark body at the pixel scale it cannot be separated; this is a cross-section, not
  the tendon's course. It relates to none of the twelve categories directly. The sartorius is
  defined next, from this tendon's physical places.
- SARTORIUS: the long strap muscle of the inner thigh, whose tendon joins the gracilis's and
  the semitendinosus's on the anteromedial tibia, in front of and on the inner side of them
  (LaPrade et al. 2007, the medial knee; the pes anserinus source in
  data/readings/definitions-20261015/remaining-anatomy-reading.md). It is muscle higher up, so on
  the knee's middle axial it is no tendon's dark oval but a flat grey sheet of muscle, brighter
  than the fat suppressed round it. Seen on the inspected prototype pictures, 2026-10-16
  (sartorius-middle-overview.png and -close.png, the proof's middle axial, slice 16, fat
  suppressed): a flattened grey body on the knee's inner side, in front of where the gracilis
  lies, a substantial sheet, with a small bright vessel beside it and a lobe behind it that the
  rule takes in. The middle axial is the standard first slice (Rohan, 2026-10-15), and the
  gracilis is named on another slice of the series, 20 mm from it on the proof, so its places are
  only a LOCATION TARGET on this one, not the cord's boundary on this slice. Its descriptions, each one check
  with its code (`sartorius_on_slice`, `name_sartorius`):
  1. the leg runs through the slice's plane, as on an axial slice, and the sequence is
     fat-suppressed and fluid-sensitive, the one the grey sheet's light was read on
     (abstain_leg_runs_in_the_plane; abstain_requires_fluid_sensitive_fat_suppression);
  2. a gracilis was named by its own lens on the semimembranosus tendon's slice, the first such
     among the study's early records of that group, its places put in the scanner's millimetres
     once and handed on (`gracilis_source`; abstain_no_native_gracilis;
     abstain_gracilis_source_geometry_unreadable), and the header names the knee, so its inner
     side is known (abstain_header_names_no_knee);
  3. those places are projected along this slice's normal, however far off its plane they lie
     (`projected_places`): the target (abstain_gracilis_projects_outside_the_picture);
  4. relative lightness (`local_lightness`): the light after a `SAMPLING_PIXELS` median, over the
     median of the seen, not-low light of the surrounding window `LOCAL_CONTRAST_MM` across on each
     axis, the window's pixel count read from the slice's own pixel pitch and made odd. Places
     the lens reads as low signal, that are not finite or that lie in the black margin have no
     reading, never a dark one, and are left out of every surround; an empty surround, or one
     whose median is zero, gives NaN, not a ratio (abstain_no_local_contrast);
  5. the muscle-grey bodies (`muscle_grey_bodies`): the places whose relative lightness lies in
     `MUSCLE_GREY` (from the lower bound up to, not including, the upper), after an opening by a
     `SAMPLING_PIXELS` square, as whole 8-connected bodies (abstain_no_soft_tissue_grey_body);
  6. a body's mean lies on the knee's inner side of the target's mean and in front of it, both
     read from the patient's axes (abstain_no_grey_body_medial_to_and_in_front_of_the_gracilis_target);
  7. and it reaches within `GRACILIS_REACH_MM` of the target in physical distance
     (abstain_no_grey_body_within_reach_of_the_gracilis_target);
  8. of those it is the largest, whole; two of exactly the largest size abstain
     (abstain_tied_largest_bodies).
  What the baseline constants are. They are explicit baseline common-sense readings of this
  kind of scan, not universal MRI biology and not a parameter fit; none was searched or tuned.
  `LOCAL_CONTRAST_MM` is a surround wider than any small tendon, vessel or muscle sheet here is
  thick, so the surround is mostly the tissue round the sheet and not the sheet; `MUSCLE_GREY` is
  Claude's reading of the first visual comparison on the proof's axial: the fat suppressed to
  about 60 to 90, muscle about 130 to 175, and white things (vessel wall, cartilage, fluid) 250
  and up, which against such a surround is a ratio from 1.5 up to, not including, 3;
  `GRACILIS_REACH_MM` is a broad locational allowance between a target that is only projected and
  a sheet, not a size and not an attachment; `SAMPLING_PIXELS` is the native sampling lens (the
  pixel either side), not an anatomical dimension. Every reading actually computed is kept as
  an array (the target, the smoothed light, the surround, the relative lightness, the labelled
  bodies, their means, sizes, reaches and status), and a reading is present only once the rule
  reached it. Limitations, stated and not chased: it localizes the sheet on one slice, not the
  muscle's course or thickness; it takes in a small vessel's halo and a lobe behind the sheet;
  the target's distance from the slice is only reported (`gracilis_source_separation_mm`), and a
  source far from the slice is no claim that the gracilis runs there. It relates to none of the
  twelve categories directly.
- GASTROCNEMIUS-SEMIMEMBRANOSUS BURSA: the fluid-filled pocket between the medial
  gastrocnemius and semimembranosus tendon. Descriptions (bursa_code):
  1. fluid is bright on this fat-suppressed, fluid-sensitive axial slice
     (abstain_fluid_not_bright_on_this_sequence);
  2. the semimembranosus tendon is named on its existing tibial-top slice
     (abstain_no_semimembranosus_tendon; on a middle slice,
     abstain_requires_the_semimembranosus_slice);
  3. the existing region rule locates the posterior field behind the inner condyle
     (abstain_no_region_behind_the_inner_condyle); it is a coarse target, not an exact muscle mask;
  4. the bursa's fluid is the largest connected white body on the knee's inner side, with its
     middle behind the tendon and before the posterior field's middle, reaching that field
     through the existing shell/contact allowance (abstain_no_fluid_body_in_the_bursal_place).
  White uses the existing fluid/marrow contrast against the carried bone places on this slice.
  Its narrow neck can be dimmer than the fluid level; direct contact between the bright body and
  the tendon is not required. The separate mask retains the body without erasing a neighbouring
  tissue label. The fluid-filled part, not the full bursal wall or its neck across slices, is
  resolved here. The relation is Baker's; this step does not diagnose a cyst.
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
  fibula?»). It is named on its main slice, the one where its region is largest (`main_slice`).
  Where that slice is looked for is pointed by cheap readings and never found by the lens on every
  slice: the squint's tiles bound a corridor (`fibula_corridor`: below the tibia's top, on the outer
  side, behind the tibia's middle), and a finer block reading there (`fibula_pointer`: blocks as
  bright as the tibia, with parts thinner than `BONE_MM` rubbed away, the body that holds the
  tibia's carried places and its middle being the tibia, and any other body behind and below it
  could be the fibula) says where a body could be, as a pointer and never as the fibula. Where the
  tibia cannot be told it says unknown, not absent. The lens and the description below run only on
  the planes it points to. Its descriptions, each one check with its code (`fibula_code`):
  1. the header names the knee, so its outer side is known (abstain_header_names_no_knee);
  2. the middle slice names the tibia (abstain_no_tibia);
  3. fat is not suppressed: with it the marrow is darkened to the light of muscle
     (abstain_marrow_suppressed_with_the_fat);
  4. it is the region the lens draws there that looks like the tibia (within `LIKE_THE_TIBIA` of
     its light), at least a disc `BONE_MM` across, its middle at least `FIBULA_BELOW_MM` below the
     tibia's top and behind the tibia's middle, apart from the tibia and whole in the block
     (`fibula_on_slice`) (abstain_no_bone_like_the_tibia_below_it); where the corridor could not be
     read the refusal says so (abstain_fibula_corridor_unreadable).
  It relates to Fracture. Seen right on the proof's T2 sagittal, 2026-10-14: slice 30, the bone
  under the tibia's outer condyle, its head and neck; the profile's support there runs over slices
  27 to 33, both ends measured, and it is also found on the T1 coronal. What is saved is its section
  on the pointed plane(s), its support and what is not known, not the whole bone, which runs off
  the picture.

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


PATELLAR RETINACULA: low-signal bands from the patella to the femoral condyles, best seen on axial
images (`docs/OBJECTS_AND_CONDITIONS.md`, Extensor mechanism). On the slice through the carried
patella's centre, the two walls are read separately. Each description has its own named code:
0. the leg runs through the plane, the header names its side, and the acquisition is fluid-sensitive
and fat-suppressed (`abstain_leg_runs_in_the_plane`, `abstain_header_names_no_knee`,
`abstain_requires_fluid_sensitive_fat_suppression`). The patella's centre selects its slice by
physical place, with named refusals for missing geometry, thickness or an off-stack centre;
1. the sparse patella and femur places are carried from their named slice; `region_holding` finds
their native lens regions as reach targets only (`abstain_no_patella_carried`,
`abstain_no_femur_carried`, `abstain_no_patellar_region`, `abstain_no_femoral_region`);
2. the posterior interval runs from the patella places' mean posterior position to the strongest
existing peak inside the femur-holding region; no peak or nonpositive interval abstains
(`abstain_no_femoral_peak`, `abstain_no_posterior_interval`);
3. on each side of the patella's inner-axis middle, the largest connected white-fluid component
within the interval must reach within `SHELL_MM` of both holder regions. Those regions are not
used as masks (`abstain_no_fluid_recess_at_the_patella`);
4. on each native cross-section nearest the patient's posterior axis, the exterior strip runs
outboard from that white component's edge by at most `SHELL_MM`, within the interval, among
available nonwhite places;
5. the whole tied minimum acquired-signal band in that strip is named only if contiguous and
below the selected white component's median signal on the same section
(`abstain_no_outboard_wall_minimum`).
The positive-inner and negative-inner walls are `medial_patellar_retinaculum` and
`lateral_patellar_retinaculum`; each identified mask localizes the wall on this slice only. It does
not measure thickness or claim the retinaculum's full course. The existing 2 mm contact allowance
locates neighbouring tissue; it is not a thickness estimate. The outer-strip minimum is the lead's
reading of the visible band, with no new grey-level cutoff. They relate to none of the twelve
conditions directly.
"""

import warnings
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull, QhullError
from skimage.morphology import reconstruction

from knee.collapse.physical import PlaneFrame
from knee.compute.contracts import handed_on
from knee.objects.interiors import InteriorRegions
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
# The area of a disc `BONE_MM` across: the smallest region that is a bone's body and not a sliver.
BONE_DISC_MM2 = float(np.pi * (BONE_MM / 2.0) ** 2)
# What the outward walk to the fibular head (`lateral_to_the_head`) says of each slice it was asked
# about: 0 never read (its area stays NaN, which is not the same as measured empty).
HEAD_SLICE_STATUS = {
    "unread": 0,
    "head_still_a_disc": 1,
    "head_no_longer_a_disc": 2,
    "head_unreadable": 3,
}
FIBULA_POINTER_STATUS = {
    "not_read": 0,
    "none": 1,
    "body": 2,
    "unreadable": 3,
    "cut": 4,
}
# A muscle's belly about the knee is centimetres across (the vasti, the hamstrings, the
# gastrocnemius, the tibialis anterior); its tendons, the fascia and the vessels among the muscles
# are millimetres (anatomy). Claude's reading of the proof's T1 coronal, 2026-10-15: of the places
# darker than fat, the bodies at least 10 mm across are the three grey bellies on the slice, and at
# 5 mm the round tendons beside the joint's inner side come in too.
MUSCLE_MM = 10.0
VESSEL_BODY_MM = 2.0
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
# The sartorius is read from baseline common-sense readings of the proof's fat-suppressed axial
# (Claude, 2026-10-16), not universal MRI biology and not a fit: the surround a sheet's light is
# weighed against is `LOCAL_CONTRAST_MM` across, wider than any small tendon, vessel or muscle
# sheet is thick; `SAMPLING_PIXELS` is the native sampling lens, the pixel either side, not an
# anatomical size; muscle's light against its surround is `MUSCLE_GREY`, from the first visual
# comparison (fat suppressed about 60 to 90, muscle 130 to 175, white things 250 and up), a ratio
# from the first bound up to, not including, the second; `GRACILIS_REACH_MM` is a broad
# locational allowance to a target that is only projected.
LOCAL_CONTRAST_MM = 20.0
SAMPLING_PIXELS = 3
MUSCLE_GREY = (1.5, 3.0)
GRACILIS_REACH_MM = 10.0
# What `sartorius_on_slice` says of each muscle-grey body it weighed.
SARTORIUS_BODY_STATUS = {
    "not_medial_and_in_front": 0,
    "beyond_reach": 1,
    "within_reach": 2,
    "selected": 3,
}
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
    "joint_capsule": 28,
    "gastrocnemius_semimembranosus_bursa": 29,
    "lateral_gastrocnemius": 30,
    "popliteal_artery": 31,
    "popliteal_vein": 32,
    "semitendinosus": 33,
    "quadriceps_fat_pad": 34,
    "prefemoral_fat_pad": 35,
    "medial_patellar_retinaculum": 36,
    "lateral_patellar_retinaculum": 37,
    "popliteus_tendon": 38,
    "iliotibial_band": 39,
    "biceps_femoris_tendon": 40,
    "gracilis": 41,
    "sartorius": 42,
}
RETINACULA = (
    "medial_patellar_retinaculum",
    "lateral_patellar_retinaculum",
)
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
    "joint_capsule",
    "gastrocnemius_semimembranosus_bursa",
    "popliteal_artery",
    "popliteal_vein",
    "semitendinosus",
    "quadriceps_fat_pad",
    "prefemoral_fat_pad",
    "patellar_retinacula",
    *RETINACULA,
    "popliteus_tendon",
    "iliotibial_band",
    "biceps_femoris_tendon",
    "gracilis",
    "sartorius",
)
FOUR_NEIGHBOURS = ndi.generate_binary_structure(2, 1)
EIGHT_NEIGHBOURS = ndi.generate_binary_structure(2, 2)


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


def axial_mcl_components(
    measurement: dict[str, Any],
    bone_supports: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Select the largest contacted positive-enclosure component without assigning unknown bone.

    The measurement is produced by ``enclosed_components_at_source``. A supplied femur or tibia
    mask is usable only when its caller has validated the native acquisition and slice address;
    missing or malformed context is retained as unknown and never excludes a component.
    """
    measured_status = measurement.get("status")
    if measured_status not in {"complete", "partial_reading"}:
        return {
            "status": "measurement_" + str(measured_status or "status_missing"),
            "selected": None,
            "measurement_status": measured_status,
        }
    labels = measurement.get("labels")
    if (
        not isinstance(labels, np.ndarray)
        or labels.ndim != 2
        or labels.dtype.kind not in "iu"
        or np.any(labels < 0)
    ):
        return {"status": "malformed_component_measurement", "selected": None}
    distance = measurement.get("distance_to_target_mm")
    if not isinstance(distance, np.ndarray) or distance.shape != labels.shape:
        return {"status": "malformed_component_measurement", "selected": None}
    rows = measurement.get("components")
    if not isinstance(rows, list):
        return {"status": "malformed_component_measurement", "selected": None}
    positive_ids = np.unique(labels[labels > 0]).astype(int).tolist()
    if positive_ids != list(range(1, len(positive_ids) + 1)):
        return {"status": "malformed_component_measurement", "selected": None}
    component_sizes = np.bincount(
        labels.ravel(), minlength=int(labels.max(initial=0)) + 1
    )
    try:
        row_ids = [row["label"] for row in rows]
        if (
            any(type(value) is not int for value in row_ids)
            or sorted(row_ids) != positive_ids
        ):
            return {"status": "malformed_component_measurement", "selected": None}
        for row in rows:
            pixels = row.get("pixels")
            label = row["label"]
            if (
                type(pixels) is not int
                or pixels <= 0
                or pixels != int(component_sizes[label])
            ):
                return {"status": "malformed_component_measurement", "selected": None}
    except (TypeError, KeyError):
        return {"status": "malformed_component_measurement", "selected": None}

    conflicts = np.zeros(labels.shape, dtype=bool)
    context_rows: dict[str, dict[str, Any]] = {}
    max_label = int(labels.max(initial=0))
    intersections: dict[str, np.ndarray] = {}
    for bone in ("femur", "tibia"):
        context = (bone_supports or {}).get(bone)
        if not isinstance(context, dict):
            context_rows[bone] = {"status": "unknown_native_support_unavailable"}
            continue
        mask = context.get("mask")
        status = context.get("status")
        if (
            status != "resolved_native_support"
            or not isinstance(mask, np.ndarray)
            or mask.shape != labels.shape
            or mask.dtype.kind != "b"
        ):
            context_rows[bone] = {
                "status": (
                    "unknown_malformed_native_support"
                    if status == "resolved_native_support"
                    else str(status or "unknown_native_support_unavailable")
                ),
                "reason": "mask_shape_or_dtype_mismatch"
                if status == "resolved_native_support"
                else None,
                "metadata": context.get("metadata"),
                "reasons": context.get("reasons", ()),
            }
            continue
        conflicts |= mask
        intersections[bone] = np.bincount(labels[mask].ravel(), minlength=max_label + 1)
        context_rows[bone] = {
            "status": status,
            "metadata": context.get("metadata"),
        }

    component_rows = []
    eligible: list[tuple[int, int]] = []
    contacted = []
    for row in rows:
        component_id = row["label"]
        bone_overlaps = {
            bone: int(counts[component_id]) for bone, counts in intersections.items()
        }
        overlap = sum(bone_overlaps.values())
        within = bool(row.get("within_existing_contact_shell"))
        component_row = {
            **row,
            "known_bone_intersection_pixels": overlap,
            "bone_intersection_pixels": bone_overlaps,
            "excluded_by_resolved_bone": bool(overlap),
        }
        component_rows.append(component_row)
        if within:
            contacted.append(component_id)
            if not overlap:
                eligible.append((component_id, int(row["pixels"])))

    result: dict[str, Any] = {
        "measurement_status": measured_status,
        "scope_partial": bool(measurement.get("partial_reading")),
        "components": component_rows,
        "bone_context": context_rows,
        "known_bone_conflict_mask": conflicts,
        "contacted_component_ids": contacted,
        "eligible_component_ids": [row[0] for row in eligible],
        "selected": np.zeros(labels.shape, dtype=bool),
        "selected_component_id": None,
        "selected_pixels": 0,
        "selected_touches_crop_edge": False,
        "selected_touches_unavailable_boundary": False,
    }
    if not component_rows:
        result["status"] = "measured_empty"
        return result
    if not contacted:
        result["status"] = (
            "contact_unknown_partial_source"
            if measurement.get("available_target_pixels")
            != measurement.get("target_pixels")
            else "no_contacted_component"
        )
        return result
    if not eligible:
        result["status"] = "candidate_merged_with_resolved_bone"
        return result
    largest = max(pixels for _, pixels in eligible)
    winners = [(label, pixels) for label, pixels in eligible if pixels == largest]
    if len(winners) != 1:
        result["status"] = "tied_largest_nonconflicting_components"
        result["largest_component_ids"] = [label for label, _ in winners]
        result["largest_component_pixels"] = largest
        return result

    label, pixels = winners[0]
    selected = labels == label
    edge = np.zeros(labels.shape, dtype=bool)
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    touches_edge = bool(np.any(selected & edge))
    selected_row = next(row for row in rows if row["label"] == label)
    touches_unknown = bool(selected_row.get("touches_unavailable_boundary"))
    result.update(
        selected=selected,
        selected_component_id=label,
        selected_pixels=pixels,
        selected_touches_crop_edge=touches_edge,
        selected_touches_unavailable_boundary=touches_unknown,
    )
    result["status"] = (
        "partial_reading" if touches_edge or touches_unknown else "identified"
    )
    return result


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
    return projected_places(points[near], frame, shape)


def projected_places(
    points_lps: np.ndarray, frame: PlaneFrame, shape: tuple[int, int]
) -> np.ndarray:
    """The pixels of a slice that places in the scanner's millimetres project onto along its normal,
    however far off its plane they lie (`places_on_slice` keeps only those within half its
    thickness, and calls this for them); a place whose projection falls outside the picture holds
    no pixel. Empty for no places; a malformed array is `PlaneFrame.to_native`'s ValueError."""
    held = np.zeros(shape, dtype=bool)
    points = np.asarray(points_lps, dtype=np.float64)
    if points.size == 0:
        return held
    rc = np.rint(frame.to_native(points)).astype(int)
    inside = (
        (rc[:, 0] >= 0)
        & (rc[:, 0] < shape[0])
        & (rc[:, 1] >= 0)
        & (rc[:, 1] < shape[1])
    )
    held[rc[inside, 0], rc[inside, 1]] = True
    return held


def region_holding(labels: np.ndarray, places: np.ndarray) -> np.ndarray:
    """The region the lens draws that holds most of the given places; empty when none holds any."""
    held = labels[places & (labels > 0)]
    if not held.size:
        return np.zeros(labels.shape, dtype=bool)
    return labels == int(np.argmax(np.bincount(held)))


def convex_envelope(
    mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Rasterize the convex hull of a 2-D mask's pixel centres.

    The hull half-plane test allows only floating-point roundoff, scaled to the native
    coordinate and equation magnitudes. This tolerance is numerical, not anatomical.
    """
    places = np.asarray(mask, dtype=bool)
    if places.ndim != 2:
        raise ValueError("convex_envelope expects a 2-D mask")
    vertices = np.empty((0, 2), dtype=np.int32)
    equations = np.empty((0, 3), dtype=np.float64)
    envelope = np.zeros(places.shape, dtype=bool)
    points = np.argwhere(places)
    if len(points) < 3:
        return envelope, vertices, equations, "abstain_fewer_than_three_points"
    try:
        hull = ConvexHull(points)
    except QhullError:
        return envelope, vertices, equations, "abstain_no_area"
    if not hull.volume > 0.0:
        return envelope, vertices, equations, "abstain_no_area"

    vertices = points[hull.vertices].astype(np.int32, copy=False)
    equations = hull.equations.astype(np.float64, copy=True)
    rows, cols = np.indices(places.shape, dtype=np.float64)
    envelope[:] = True
    epsilon = np.finfo(np.float64).eps
    max_row = max(places.shape[0] - 1, 0)
    max_col = max(places.shape[1] - 1, 0)
    for a, b, c in equations:
        residual = a * rows + b * cols + c
        scale = abs(a) * max_row + abs(b) * max_col + abs(c) + 1.0
        envelope &= residual <= epsilon * scale * 64.0
    return envelope, vertices, equations, "measured"


def popliteus_in_notch(
    femur: np.ndarray, lcl: np.ndarray
) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
    """Select the largest LCL-region component in the femoral convex-envelope concavity."""
    femur_places = np.asarray(femur, dtype=bool)
    lcl_places = np.asarray(lcl, dtype=bool)
    if femur_places.ndim != 2 or lcl_places.ndim != 2:
        raise ValueError("popliteus_in_notch expects 2-D masks")
    if femur_places.shape != lcl_places.shape:
        raise ValueError("femur and LCL masks must have the same shape")
    empty = np.zeros(femur_places.shape, dtype=bool)
    readings: dict[str, np.ndarray] = {
        "envelope": empty.copy(),
        "vertices": np.empty((0, 2), dtype=np.int32),
        "equations": np.empty((0, 3), dtype=np.float64),
        "candidate": empty.copy(),
        "candidate_labels": np.zeros(femur_places.shape, dtype=np.int32),
        "selected_component": empty.copy(),
        "convex_envelope_code": np.asarray("not_measured"),
    }
    if not femur_places.any():
        return empty, readings, "abstain_no_femoral_region"
    if not lcl_places.any():
        return empty, readings, "abstain_no_lcl_region"

    envelope, vertices, equations, envelope_code = convex_envelope(femur_places)
    readings["envelope"] = envelope
    readings["vertices"] = vertices
    readings["equations"] = equations
    readings["convex_envelope_code"] = np.asarray(envelope_code)
    if envelope_code != "measured":
        return empty, readings, "abstain_no_lateral_femoral_notch"

    candidate = envelope & ~femur_places & lcl_places
    components, count = ndi.label(candidate, structure=FOUR_NEIGHBOURS)
    readings["candidate"] = candidate
    readings["candidate_labels"] = components.astype(np.int32, copy=False)
    if count == 0:
        return empty, readings, "abstain_no_lateral_femoral_notch"
    sizes = np.bincount(components.ravel(), minlength=count + 1)
    selected_id = int(np.argmax(sizes[1:]) + 1)
    selected = components == selected_id
    readings["selected_component"] = selected
    return selected, readings, "identified"


def itb_code(
    sides_in_plane: bool,
    leg_in_plane: bool,
    knee: str,
    fat_suppressed: bool,
    reading: str,
) -> str:
    """Whether the ITB was named on a slice, or why not: each check is one of its descriptions.
    `reading` is what `iliotibial_band` said of the slice's own measurements."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not leg_in_plane:
        return "abstain_leg_runs_through_the_plane"
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if fat_suppressed:
        return "abstain_not_parted_from_the_fat_with_fat_suppression"
    return reading


def iliotibial_band(
    plane: np.ndarray,
    fat: np.ndarray,
    femur: np.ndarray,
    tibia: np.ndarray,
    outside: np.ndarray,
    available: np.ndarray,
    outward_mm: np.ndarray,
    up_mm: np.ndarray,
    to_tibia_mm: np.ndarray,
    leg_axis: int,
) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
    """The iliotibial band as the dark fascial line on the deep surface of the leg's outer
    subcutaneous fat, from the thigh down to the tibia.

    Chien et al. 2020: the ITB is the deep fascia of the thigh continued down the outside of the
    knee to the tibia, «a broad, thick band of low signal». It lies directly under the fat, so on
    each native cross-section across the leg (a line of pixels; `leg_axis` is the native axis the
    leg runs along, the sections' index) the rule reads:

    - the layer: the named subcutaneous fat lying outboard of the bones on that section
      (`outward_mm` is each place's position toward the knee's outer side);
    - the strip: the places not fat, bone, air, skin or unavailable, deeper than the layer's deep
      edge by at most `SHELL_MM`, the reach the rules already allow a thin dark band to its
      neighbour; the deep neighbour is the next `SHELL_MM` beyond it;
    - the line: the strip's lowest acquired signal, kept whole when its tied minimum is one
      contiguous run, and only when it is darker than the median light of the layer and of the deep
      neighbour, so it is a dip between two lighter tissues, not the first step of a slope from fat
      to muscle. No cutoff, no smoothing, no interpolation across sections.

    The band is kept from the top of the picture down to the most superior section where a line
    comes within `SHELL_MM` of the tibia, its insertion (Gerdy's tubercle); below it the line goes
    on as the leg's crural fascia, which is not named. It must pass a section holding the femur.
    A one-pixel trace of the band's course is measured, not its thickness, nor the exact insertion.
    Returns the mask, the retained readings and the code.
    """
    shape = plane.shape
    maps = (fat, femur, tibia, outside, available, outward_mm, up_mm, to_tibia_mm)
    if (
        plane.ndim != 2
        or any(np.shape(m) != shape for m in maps)
        or leg_axis not in (0, 1)
    ):
        raise ValueError(
            "iliotibial_band expects same-shaped 2-D maps and a native axis 0 or 1"
        )

    def across(values: np.ndarray) -> np.ndarray:
        """Rows are the sections, whichever native axis the leg runs along (its own inverse)."""
        return values if leg_axis == 0 else values.T

    light, fat_s, outside_s, ok_s = (
        across(plane),
        across(np.asarray(fat, dtype=bool)),
        across(np.asarray(outside, dtype=bool)),
        across(np.asarray(available, dtype=bool)),
    )
    femur_s, tibia_s = (
        across(np.asarray(femur, dtype=bool)),
        across(np.asarray(tibia, dtype=bool)),
    )
    out_s, up_s, near_tibia = across(outward_mm), across(up_mm), across(to_tibia_mm)
    bones = femur_s | tibia_s
    count = light.shape[0]
    layer = np.zeros(light.shape, dtype=bool)
    strip = np.zeros(light.shape, dtype=bool)
    lines = np.zeros(light.shape, dtype=bool)
    # per section: 0 no layer, 1 line, 2 tied minima apart, 3 no dip, 4 no strip or deep neighbour
    status = np.zeros(count, dtype=np.int8)
    deep_edge = np.full(count, np.nan)
    layer_light = np.full(count, np.nan)
    line_light = np.full(count, np.nan)
    deep_light = np.full(count, np.nan)
    section_up = up_s.mean(axis=1)
    readings: dict[str, np.ndarray] = {}

    def finish(mask_s: np.ndarray, stop_up: float, code: str):
        readings.update(
            fat_layer=across(layer),
            strip=across(strip),
            candidate_lines=across(lines),
            section_axis=np.asarray(leg_axis, dtype=np.int8),
            section_status=status,
            section_fat_deep_edge_mm=deep_edge,
            section_fat_light=layer_light,
            section_line_light=line_light,
            section_deep_light=deep_light,
            distal_stop_up_mm=np.asarray(stop_up, dtype=np.float64),
        )
        return across(mask_s), readings, code

    nothing = np.zeros(light.shape, dtype=bool)
    if not fat_s.any():
        return finish(nothing, np.nan, "abstain_no_subcutaneous_fat")
    if not (femur_s.any() and tibia_s.any()):
        return finish(nothing, np.nan, "abstain_no_femur_and_tibia")
    # each section's outermost bone place; infinite where it holds none
    edge = np.full(count, np.inf)
    for i in np.flatnonzero(bones.any(axis=1)):
        edge[i] = out_s[i][bones[i]].max()
    layer = fat_s & ok_s & (out_s > edge[:, None])
    if not layer.any():
        return finish(nothing, np.nan, "abstain_no_fat_outside_the_bones")

    reach = float(SHELL_MM)
    for i in np.flatnonzero(layer.any(axis=1)):
        under = out_s[i][layer[i]].min()  # the layer's deep edge
        gap = under - out_s[i]  # how far deeper than the edge, millimetres
        usable = ok_s[i] & ~outside_s[i] & ~fat_s[i]
        strip[i] = usable & ~bones[i] & (gap > 0.0) & (gap <= reach)
        beyond = usable & (gap > reach) & (gap <= 2.0 * reach)
        deep_edge[i] = under
        layer_light[i] = float(np.median(light[i][layer[i]]))
        if not strip[i].any() or not beyond.any():
            status[i] = 4
            continue
        lowest = float(light[i][strip[i]].min())
        tied = strip[i] & (light[i] == lowest)
        # the tied places in order across the section
        along = tied[np.argsort(out_s[i])].astype(np.int8)
        line_light[i] = lowest
        deep_light[i] = float(np.median(light[i][beyond]))
        if np.count_nonzero(np.diff(np.r_[0, along]) == 1) != 1:
            status[i] = 2
        elif lowest < layer_light[i] and lowest < deep_light[i]:
            status[i] = 1
            lines[i] = tied
        else:
            status[i] = 3
    if not lines.any():
        return finish(nothing, np.nan, "abstain_no_dark_line_deep_to_the_fat")

    reaching = np.flatnonzero((lines & (near_tibia <= reach)).any(axis=1))
    if not reaching.size:
        return finish(nothing, np.nan, "abstain_band_does_not_reach_the_tibia")
    # the most superior section where a line reaches the tibia
    stop_up = float(section_up[reaching].max())
    kept = lines & (section_up >= stop_up)[:, None]
    if not (kept.any(axis=1) & femur_s.any(axis=1)).any():
        return finish(nothing, stop_up, "abstain_band_not_beside_the_femur")
    return finish(kept, stop_up, "identified")


def iliotibial_band_on_slice(
    plane: np.ndarray,
    objects: np.ndarray,
    available: np.ndarray,
    basis_lps: np.ndarray,
    knee: str,
    fat_suppressed: bool,
    measures: Measures | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
    """The ITB on one slice (its paragraph in the module note): the slice must be a coronal one
    (side to side and the leg both in its plane), the header must name the knee so its outer side is
    known, fat must not be suppressed (the layer is the named subcutaneous fat, which the sequences
    without suppression name; the partner lays it onto the other), on the existing middle coronal. Of the slice's named parts it reads the
    subcutaneous fat, the femur, the tibia, the air and the skin. `measures` are the slice's shared
    measures, when its caller keeps them: each place's position toward the left and along the leg,
    and its distance from the tibia, are read from them. Returns the mask, the retained readings
    (empty where a prerequisite refused before anything was measured) and the code."""
    shape = plane.shape
    sides, _, leg = axes_in_plane(basis_lps)
    tibia = objects == OBJECT_CODES["tibia"]
    refusal = itb_code(sides, leg, knee, fat_suppressed, "identified")
    if refusal != "identified":
        return np.zeros(shape, dtype=bool), {}, refusal
    spacing_rc = np.linalg.norm(basis_lps, axis=0)
    if measures is None:
        left = positions_along(shape, basis_lps, 0)
        up = positions_along(shape, basis_lps, 2)
        to_tibia = (
            distance_from(tibia, spacing_rc) if tibia.any() else np.full(shape, np.inf)
        )
    else:
        left, up = measures.along(0), measures.along(2)
        to_tibia = (
            measures.distance(tibia, spacing_rc)
            if tibia.any()
            else np.full(shape, np.inf)
        )
    # the outer side is the patient's right for a right knee, whose left axis points inward
    outer = -1.0 if knee == "R" else 1.0
    mask, readings, reading = iliotibial_band(
        plane,
        objects == OBJECT_CODES["subcutaneous_fat"],
        objects == OBJECT_CODES["femur"],
        tibia,
        np.isin(objects, (OBJECT_CODES["air"], OBJECT_CODES["skin"])),
        available,
        outer * left,
        up,
        to_tibia,
        int(np.argmax(np.abs(np.asarray(basis_lps)[2]))),
    )
    return (
        mask,
        readings,
        itb_code(sides, leg, knee, fat_suppressed, reading),
    )


def unique_largest(sizes: np.ndarray) -> int | None:
    """The index of the one largest size; None when there are none or the largest is shared, since
    two bodies of exactly the same size are not told apart by their size."""
    sizes = np.asarray(sizes)
    if not sizes.size:
        return None
    winners = np.flatnonzero(sizes == sizes.max())
    return int(winners[0]) if len(winners) == 1 else None


def white_body_at_location(
    white: np.ndarray | None, target: np.ndarray | None
) -> tuple[np.ndarray, str, dict[str, np.ndarray]]:
    """Keep the whole largest 8-connected white body that intersects its location target.

    The target identifies where to ask; it is not a boundary for the body. No target or no
    intersecting body returns an empty mask, and equal largest eligible bodies remain tied.
    Labels, component sizes, eligible labels and the largest eligible labels are retained for
    either result. Missing inputs are empty on the other input's shape; empty dimensions are
    valid. Non-boolean or non-2D inputs and mismatched shapes are rejected.
    """

    def as_mask(value: np.ndarray | None, name: str) -> np.ndarray | None:
        if value is None:
            return None
        mask = np.asarray(value)
        if mask.ndim != 2 or mask.dtype != np.bool_:
            raise ValueError(f"{name} must be a two-dimensional boolean mask")
        return mask

    white_mask = as_mask(white, "white")
    target_mask = as_mask(target, "target")
    if (
        white_mask is not None
        and target_mask is not None
        and white_mask.shape != target_mask.shape
    ):
        raise ValueError("white and target masks must have the same shape")
    shape = (
        white_mask.shape
        if white_mask is not None
        else target_mask.shape
        if target_mask is not None
        else (0, 0)
    )
    if white_mask is None:
        white_mask = np.zeros(shape, dtype=bool)
    if target_mask is None:
        target_mask = np.zeros(shape, dtype=bool)

    if white_mask.size:
        labels, component_count = ndi.label(
            white_mask, structure=np.ones((3, 3), dtype=bool)
        )
        sizes = np.bincount(labels.ravel(), minlength=component_count + 1)[1:]
    else:
        labels = np.zeros(shape, dtype=np.int32)
        sizes = np.zeros(0, dtype=np.int64)
    eligible_ids = np.unique(labels[target_mask])
    eligible_ids = eligible_ids[eligible_ids > 0].astype(np.int64, copy=False)
    winner_ids = np.zeros(0, dtype=np.int64)
    selected = np.zeros(shape, dtype=bool)
    if not target_mask.any():
        code = "no_target"
    elif not eligible_ids.size:
        code = "no_body_at_target"
    else:
        eligible_sizes = sizes[eligible_ids - 1]
        largest = int(np.max(eligible_sizes))
        winner_ids = eligible_ids[eligible_sizes == largest]
        winner_index = unique_largest(eligible_sizes)
        if winner_index is None:
            code = "tied_largest_bodies"
        else:
            winner_id = int(eligible_ids[winner_index])
            selected = labels == winner_id
            code = "selected"
    readings = {
        "labels": labels,
        "sizes": sizes,
        "eligible_ids": eligible_ids,
        "winner_ids": winner_ids,
    }
    return selected, code, readings


def twin_marrow_light(twin: np.ndarray, places: np.ndarray) -> float:
    """The marrow's light in the fat-suppressed twin laid on a slice's pixels (NaN where it has no
    say) over a bone's places: the median of the places it sees, NaN when it sees none."""
    seen = np.asarray(places, dtype=bool) & np.isfinite(twin)
    return float(np.median(twin[seen])) if seen.any() else float("nan")


def fibula_like_head(
    plane: np.ndarray, target: np.ndarray, light: float
) -> tuple[np.ndarray, str]:
    """The fibular head's body on one fat-bright slice: the region as bright as the fibula's own
    marrow (within `LIKE_THE_TIBIA` of `light`) that holds most of `target`, the fibula's places
    projected onto the slice (`projected_places`). Specks and bridges narrower than three native
    pixels are taken out first, by one erosion and dilation with a 3 x 3 square: a sampling-scale
    operation, whose reach in millimetres is the pixel pitch and not an anatomical size, and which
    being an opening closes no crack and fills no hole. Returns the mask and
    its code; the mask is empty, and nothing is made up, when `light` is not finite and positive,
    the target is empty, no body holds a place of it, or two bodies hold exactly as many."""
    values = np.asarray(plane, dtype=np.float64)
    places = np.asarray(target, dtype=bool)
    if values.ndim != 2 or places.shape != values.shape:
        raise ValueError("head_inputs_must_share_a_2d_shape")
    none = np.zeros(values.shape, dtype=bool)
    if not (np.isfinite(light) and light > 0):
        return none, "abstain_no_fibula_marrow_light"
    if not places.any():
        return none, "abstain_no_projected_fibula"
    low, high = LIKE_THE_TIBIA
    like = ndi.binary_opening(
        (values >= low * light) & (values <= high * light),
        structure=np.ones((3, 3), dtype=bool),
    )
    bodies, _ = ndi.label(like)
    held = bodies[places & (bodies > 0)]
    if not held.size:
        return none, "abstain_no_marrow_like_body_at_the_fibula"
    holds = np.bincount(held)[1:]
    winner = unique_largest(holds)
    if winner is None:
        return none, "abstain_tied_head_bodies"
    return bodies == winner + 1, "identified"


def head_area_mm2(head: np.ndarray, code: str, spacing_rc: np.ndarray) -> float:
    """What `fibula_like_head` says of the head's area in square millimetres: its area when named;
    0.0 when the fibula's places held no marrow-like body (measured: the head is gone there); NaN
    where it cannot be said (no light, the fibula projects outside the picture, a tie, or no
    usable pixel pitch)."""
    spacing = np.asarray(spacing_rc, dtype=np.float64)
    if (
        spacing.shape != (2,)
        or not np.all(np.isfinite(spacing))
        or np.any(spacing <= 0)
    ):
        return float("nan")
    if code == "identified":
        return float(np.count_nonzero(head)) * float(np.prod(spacing))
    if code == "abstain_no_marrow_like_body_at_the_fibula":
        return 0.0
    return float("nan")


def lateral_to_the_head(
    fibula_lps: np.ndarray,
    origins_lps: np.ndarray,
    normal: np.ndarray,
    thicknesses_mm: Sequence[float | None],
    knee: str,
    head_area_at: Callable[[int], float],
) -> tuple[int | None, np.ndarray, np.ndarray, str]:
    """The slice just beyond the fibular head's lateral face, by the walk the module note describes:
    from the slice through the fibula's places (`slice_through`), outward toward the knee's outer
    side while the head's body is still at least `BONE_DISC_MM2`; the answer is the first slice
    where it is not. `head_area_at(z)` is the head's area on slice z in square millimetres (NaN
    where it cannot be said; `head_area_mm2`), asked of a slice only when the walk reaches it, and
    the caller keeps whatever it made there, so nothing is made twice. `origins_lps` (Z, 3) are the
    slices' origins and `normal` the series' normal; `knee` is the header's "R" or "L".

    Returns (index or None, area per slice, status per slice, code). A slice the walk never read
    keeps NaN in the areas and `HEAD_SLICE_STATUS["unread"]` in the status."""
    origins = np.asarray(origins_lps, dtype=np.float64)
    places = np.asarray(fibula_lps, dtype=np.float64)
    if origins.ndim != 2 or origins.shape[1] != 3 or not np.all(np.isfinite(origins)):
        raise ValueError("invalid_slice_origins")
    count = len(origins)
    if len(thicknesses_mm) != count:
        raise ValueError("thicknesses_must_match_the_slices")
    axis = np.asarray(normal, dtype=np.float64)
    if axis.shape != (3,) or not np.all(np.isfinite(axis)) or not np.any(axis):
        raise ValueError("invalid_series_normal")
    axis = axis / np.linalg.norm(axis)
    areas = np.full(count, np.nan)
    status = np.zeros(count, dtype=np.int8)
    if knee not in ("R", "L"):
        return None, areas, status, "abstain_header_names_no_knee"
    if places.size == 0:
        return None, areas, status, "abstain_no_fibula"
    if places.ndim != 2 or places.shape[1] != 3 or not np.all(np.isfinite(places)):
        raise ValueError("invalid_fibula_places")
    if count < 2:
        return None, areas, status, "abstain_the_series_has_one_slice"
    if abs(float(axis[0])) < ALONG_THE_LEG:
        return None, areas, status, "abstain_slices_do_not_run_side_to_side"
    thickness = np.asarray(
        [np.nan if t is None else float(t) for t in thicknesses_mm], dtype=np.float64
    )
    if not np.all(np.isfinite(thickness)) or np.any(thickness <= 0):
        return None, areas, status, "abstain_no_slice_thickness"
    main = slice_through(places.mean(axis=0), origins, axis, list(thickness))
    if main is None:
        return None, areas, status, "abstain_no_slice_holds_the_fibula"
    # the outer side is the patient's right for a right knee, the left axis' negative
    outward = -1.0 if knee == "R" else 1.0
    along = outward * float(
        origins[min(main + 1, count - 1), 0] - origins[max(main - 1, 0), 0]
    )
    # Exact on purpose: only the sign of `along` is used, and exactly zero has none.
    if along == 0.0:  # NOSONAR(S1244)
        return None, areas, status, "abstain_slices_do_not_run_side_to_side"
    step = 1 if along > 0 else -1
    z = main
    while 0 <= z < count:
        area = float(head_area_at(z))
        areas[z] = area
        if not np.isfinite(area) or area < 0:
            status[z] = HEAD_SLICE_STATUS["head_unreadable"]
            return None, areas, status, "abstain_head_unreadable_on_the_way"
        if area < BONE_DISC_MM2:
            status[z] = HEAD_SLICE_STATUS["head_no_longer_a_disc"]
            break
        status[z] = HEAD_SLICE_STATUS["head_still_a_disc"]
        z += step
    if not 0 <= z < count:
        return None, areas, status, "abstain_the_series_ends_before_the_head_does"
    if z == main:
        return (
            None,
            areas,
            status,
            "abstain_the_fibula_is_not_a_disc_on_its_main_slice",
        )
    return z, areas, status, "identified"


def smoothed_along_the_leg(
    values: np.ndarray, basis_lps: np.ndarray, length_mm: float
) -> tuple[np.ndarray, int]:
    """The median of `values` over `length_mm` along the leg (the native axis nearer the patient's
    superior axis, read from the basis, never assumed to be the rows), and the window in pixels.
    NaN wherever any pixel of the window is not finite: a place the filter cannot fully see has no
    reading, so an unseen pixel never lowers a median into false darkness."""
    basis = np.asarray(basis_lps, dtype=np.float64)
    leg_axis = int(np.argmax(np.abs(basis[2])))
    pitch = float(np.linalg.norm(basis[:, leg_axis]))
    window = int(2 * round(length_mm / 2.0 / pitch) + 1)
    size = (window, 1) if leg_axis == 0 else (1, window)
    seen = np.isfinite(values)
    median = ndi.median_filter(np.where(seen, values, 0.0), size=size, mode="nearest")
    supported = (
        ndi.minimum_filter(seen.astype(np.uint8), size=size, mode="nearest") == 1
    )
    return np.where(supported, median, np.nan), window


def proximal_biceps_on_slice(
    plane: np.ndarray,
    twin: np.ndarray,
    basis_lps: np.ndarray,
    light: float,
    twin_light: float,
    head: np.ndarray,
    fat_suppressed: bool = False,
    measures: Measures | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
    """The proximal biceps femoris tendon on its slice (its paragraph in the module note).

    `plane` is the fat-bright sagittal slice and `twin` its fat-suppressed twin laid on the same
    pixels (NaN where it has no say); `light` and `twin_light` are the fibula's marrow light in
    each (`twin_marrow_light` for the twin's); `head` is the head's body here (`fibula_like_head`);
    `fat_suppressed` is the plane's own tag; `measures` are the slice's shared measures, when its
    caller keeps them: each place's position along the leg and its distance from the marrow, the
    head and the belly are read from them. The pixel pitch is the basis' own.

    Returns the mask, every reading actually made and the code. A reading is present only once
    the rule reached it: a refusal leaves out what it never measured instead of filling it with a
    zero that would read as measured. Every value is an ndarray, none of object dtype."""
    values = np.asarray(plane, dtype=np.float64)
    laid = np.asarray(twin, dtype=np.float64)
    places = np.asarray(head, dtype=bool)
    basis = np.asarray(basis_lps, dtype=np.float64)
    if values.ndim != 2 or laid.shape != values.shape or places.shape != values.shape:
        raise ValueError("biceps_inputs_must_share_a_2d_shape")
    if basis.shape != (3, 2) or not np.all(np.isfinite(basis)):
        raise ValueError("invalid_lps_basis")
    spacing_rc = np.linalg.norm(basis, axis=0)
    if np.any(spacing_rc <= 0):
        raise ValueError("invalid_lps_basis")
    empty = np.zeros(values.shape, dtype=bool)
    readings: dict[str, np.ndarray] = {}

    def refuse(code: str) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
        return empty, readings, code

    if not values.size:
        return refuse("abstain_empty_slice")
    if fat_suppressed:
        return refuse("abstain_marrow_as_dark_as_a_ligament_with_fat_suppression")
    _, front_in_plane, leg_in_plane = axes_in_plane(basis)
    if not front_in_plane:
        return refuse("abstain_front_to_back_runs_through_the_plane")
    if not leg_in_plane:
        return refuse("abstain_leg_runs_through_the_plane")
    if not (np.isfinite(light) and light > 0):
        return refuse("abstain_no_fibula_marrow_light")
    if not (np.isfinite(twin_light) and twin_light > 0):
        return refuse("abstain_no_suppressed_marrow_light")
    if not np.isfinite(laid).any():
        return refuse("abstain_no_twin_on_the_slice")
    if not places.any():
        return refuse("abstain_no_fibular_head_on_the_slice")

    def reach(of: np.ndarray) -> np.ndarray:
        return (
            distance_from(of, spacing_rc)
            if measures is None
            else measures.distance(of, spacing_rc)
        )

    low, high = LIKE_THE_TIBIA
    pixel_mm2 = float(np.prod(spacing_rc))
    leg_axis = int(np.argmax(np.abs(basis[2])))
    smooth, window = smoothed_along_the_leg(values, basis, LIGAMENT_THICK_MM)
    smooth_twin, _ = smoothed_along_the_leg(laid, basis, LIGAMENT_THICK_MM)
    superior = (
        positions_along(values.shape, basis, 2)
        if measures is None
        else measures.along(2)
    )
    dark = smooth <= LIGAMENT_DARKER * light
    tendon_like = dark & (smooth_twin <= twin_light)
    muscle_like = (
        dark
        & (smooth_twin > high * twin_light)
        & (smooth_twin < FLUID_BRIGHTER * twin_light)
    )
    marrow = thick_parts(values >= low * light, spacing_rc, BONE_MM) | places
    to_marrow = reach(marrow)
    to_head = reach(places)
    head_top = float(superior[places].max())
    readings.update(
        fibula_marrow_light_fat_bright=np.asarray(light, dtype=np.float64),
        fibula_marrow_light_fat_suppressed=np.asarray(twin_light, dtype=np.float64),
        smoothing_window_pixels=np.asarray(window, dtype=np.int32),
        leg_axis=np.asarray(leg_axis, dtype=np.int8),
        smoothed_fat_bright=smooth,
        smoothed_fat_suppressed_twin=smooth_twin,
        superior_mm=np.asarray(superior, dtype=np.float64),
        dark_fat_bright=dark,
        tendon_like=tendon_like,
        muscle_like=muscle_like,
        marrow_bodies=marrow,
        distance_to_marrow_mm=np.asarray(to_marrow, dtype=np.float64),
        head_region=places,
        distance_to_head_mm=np.asarray(to_head, dtype=np.float64),
        head_top_mm=np.asarray(head_top, dtype=np.float64),
    )

    # a muscle above the head: the largest body at least BONE_MM across, whole
    bodies = thick_parts(muscle_like, spacing_rc, BONE_MM)
    parts, count = ndi.label(bodies)
    readings["muscle_bodies"] = bodies
    readings["muscle_body_labels"] = parts.astype(np.int32)
    index = np.arange(1, count + 1)
    sizes = np.bincount(parts.ravel(), minlength=count + 1)[1:]
    middle = (
        np.asarray(ndi.mean(superior, parts, index=index)) if count else np.empty(0)
    )
    above = index[middle > head_top]
    if not above.size:
        return refuse("abstain_no_muscle_belly_above_the_head")
    chosen = unique_largest(sizes[above - 1])
    if chosen is None:
        return refuse("abstain_tied_muscle_bellies")
    belly = parts == above[chosen]
    muscle_bottom = float(superior[belly].min())
    readings.update(
        muscle_belly=belly,
        muscle_bottom_mm=np.asarray(muscle_bottom, dtype=np.float64),
        muscle_area_mm2=np.asarray(
            np.count_nonzero(belly) * pixel_mm2, dtype=np.float64
        ),
        distance_to_belly_mm=np.asarray(reach(belly), dtype=np.float64),
    )

    # a dark cord between them along the leg, clear of any marrow's cortex
    between = (superior < muscle_bottom) & (superior > head_top)
    candidate = thick_parts(
        tendon_like & (to_marrow > SHELL_MM) & between, spacing_rc, LIGAMENT_THICK_MM
    )
    pieces, found = ndi.label(candidate, structure=np.ones((3, 3), dtype=bool))
    readings.update(
        between_muscle_and_head=between,
        dark_piece_candidates=candidate,
        piece_labels=pieces.astype(np.int32),
        piece_count=np.asarray(found, dtype=np.int32),
    )
    if not found:
        return refuse("abstain_nothing_dark_between_the_muscle_and_the_head")
    ids = np.arange(1, found + 1)
    counts = np.bincount(pieces.ravel(), minlength=found + 1)[1:]
    area = counts * pixel_mm2
    to_belly = readings["distance_to_belly_mm"]
    reach_belly = np.asarray(ndi.minimum(to_belly, pieces, index=ids))
    reach_head = np.asarray(ndi.minimum(to_head, pieces, index=ids))
    top = np.asarray(ndi.maximum(superior, pieces, index=ids))
    bottom = np.asarray(ndi.minimum(superior, pieces, index=ids))
    competent = (
        (area >= BONE_DISC_MM2) & (reach_belly <= BONE_MM) & (reach_head <= BONE_MM)
    )
    readings.update(
        piece_area_mm2=area,
        piece_reach_to_belly_mm=reach_belly,
        piece_reach_to_head_mm=reach_head,
        piece_length_along_leg_mm=top - bottom + abs(float(basis[2, leg_axis])),
        piece_competent=competent,
    )
    if not competent.any():
        return refuse("abstain_no_competent_piece_joins_the_muscle_and_the_head")
    best = unique_largest(counts[competent])
    if best is None:
        return refuse("abstain_tied_competent_pieces")
    selected = int(ids[competent][best])
    readings["selected_piece"] = np.asarray(selected, dtype=np.int32)
    return pieces == selected, readings, "identified"


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
    plane: np.ndarray,
    objects: np.ndarray,
    measures: Measures | None = None,
    reference_light: float | None = None,
) -> np.ndarray | None:
    """On a fat-suppressed, fluid-sensitive slice, the places white as fluid: more than
    `FLUID_BRIGHTER` times as bright as the bones' marrow, the femur's and the tibia's together.
    None where the slice names no femur and tibia and no usable reference is supplied, or their
    light is none. `measures` are the
    slice's shared measures, when its caller keeps them: the bones' marrow light is read from
    them.

    `reference_light` is an optional scalar the CALLER has already validated (same series, middle
    frame and support). When it is a finite positive number it replaces the per-point
    measurement of the threshold reference and removes the local-bone prerequisite for this
    measurement. Absent or unusable (non-finite, non-positive, boolean, not a number) falls back
    to the per-point calibration exactly as before, which requires both local names."""
    light: float | None = None
    if reference_light is not None and not isinstance(
        reference_light, (bool, np.bool_)
    ):
        try:
            given = float(reference_light)
        except (TypeError, ValueError):
            given = float("nan")
        if np.isfinite(given) and given > 0:
            light = given
    if light is None:
        femur = objects == OBJECT_CODES["femur"]
        tibia = objects == OBJECT_CODES["tibia"]
        if not (femur.any() and tibia.any()):
            return None
        bones = femur | tibia
        light = (
            marrow_light(plane, bones) if measures is None else measures.light(bones)
        )
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


def capsule_at_side_recesses(
    dark: np.ndarray,
    white: np.ndarray,
    objects: np.ndarray,
    basis_lps: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> dict[str, np.ndarray]:
    """The side recesses, their dark outer walls, and the cavity-facing fluid edge.

    Each recess lies outboard of its meniscus, above the joint, beside the femur.
    Of the white bodies reaching the femur through its shell (the existing SHELL_MM
    contact allowance), use the largest on each side. The capsule is low signal just
    outside that body, away from the femur, over the body's height. The same contact
    allowance locates the wall; it does not prescribe capsule thickness.

    ``capsule`` is the original union of the two dark outer walls. ``lining`` is the
    union of the per-section cavity-facing edge pixels from each selected fluid body.
    ``negative_*`` and ``positive_*`` retain each side's selected recess, wall and
    lining masks. ``section_axis`` is the in-plane array axis most aligned with LPS
    superior/inferior. Each ``*_section_status`` is indexed along that axis and names
    one of ``no_fluid``, ``no_wall``, ``ambiguous_wall`` or ``selected``. A section
    is selected only when every same-side wall position is strictly farther outboard
    than the outermost fluid position; its lining pixels are the fluid pixels at that
    outermost position. These are local surface-location sections, not membrane
    signal, thickness or a full-course description.
    """
    femur = objects == OBJECT_CODES["femur"]
    menisci = [
        objects == OBJECT_CODES[name]
        for name in ("medial_meniscus", "lateral_meniscus")
    ]
    capsule = np.zeros(objects.shape, dtype=bool)
    lining = np.zeros(objects.shape, dtype=bool)
    outputs: dict[str, np.ndarray] = {
        "capsule": capsule,
        "lining": lining,
        "negative_recess": np.zeros(objects.shape, dtype=bool),
        "negative_wall": np.zeros(objects.shape, dtype=bool),
        "negative_lining": np.zeros(objects.shape, dtype=bool),
        "positive_recess": np.zeros(objects.shape, dtype=bool),
        "positive_wall": np.zeros(objects.shape, dtype=bool),
        "positive_lining": np.zeros(objects.shape, dtype=bool),
        "section_axis": np.asarray(
            int(np.argmax(np.abs(basis_lps[2, :]))), dtype=np.int8
        ),
    }
    section_axis = int(outputs["section_axis"])
    section_count = objects.shape[section_axis]
    for side_name in ("negative", "positive"):
        outputs[f"{side_name}_section_status"] = np.full(
            section_count, "no_fluid", dtype="<U24"
        )
    if not femur.any() or not all(mask.any() for mask in menisci):
        return outputs
    side = (
        positions_along(objects.shape, basis_lps, 0)
        if measures is None
        else measures.along(0)
    )
    up = (
        positions_along(objects.shape, basis_lps, 2)
        if measures is None
        else measures.along(2)
    )
    ends = sorted(float(np.median(side[mask])) for mask in menisci)
    joint_bottom = min(float(up[mask].min()) for mask in menisci)
    near_femur = (
        distance_from(femur, spacing_rc)
        if measures is None
        else measures.distance(femur, spacing_rc)
    ) <= SHELL_MM
    pieces, count = ndi.label(white, structure=np.ones((3, 3), dtype=bool))
    for side_name, sign, end in (
        ("negative", -1, ends[0]),
        ("positive", 1, ends[1]),
    ):
        recess = outputs[f"{side_name}_recess"]
        wall = outputs[f"{side_name}_wall"]
        side_lining = outputs[f"{side_name}_lining"]
        status = outputs[f"{side_name}_section_status"]
        candidates = []
        for region in range(1, count + 1):
            mask = pieces == region
            centre = float(np.median(side[mask]))
            if (centre - end) * sign <= 0 or np.median(up[mask]) < joint_bottom:
                continue
            if np.any(mask & near_femur):
                candidates.append((int(mask.sum()), region))
        if not candidates:
            continue
        _, region = max(candidates)
        np.equal(pieces, region, out=recess)
        outside = (side - np.median(side[recess])) * sign > 0
        beside = distance_from(recess, spacing_rc) <= SHELL_MM
        height = (up >= up[recess].min()) & (up <= up[recess].max())
        wall[:] = dark & outside & beside & height
        capsule |= wall
        for section in range(section_count):
            if section_axis == 0:
                fluid_section = recess[section, :]
                wall_section = wall[section, :]
                side_section = side[section, :]
                lining_section = side_lining[section, :]
            else:
                fluid_section = recess[:, section]
                wall_section = wall[:, section]
                side_section = side[:, section]
                lining_section = side_lining[:, section]
            if not fluid_section.any():
                status[section] = "no_fluid"
                continue
            if not wall_section.any():
                status[section] = "no_wall"
                continue
            outermost_fluid = (
                float(side_section[fluid_section].min())
                if sign < 0
                else float(side_section[fluid_section].max())
            )
            outermost_wall = (
                float(side_section[wall_section].max())
                if sign < 0
                else float(side_section[wall_section].min())
            )
            if sign * outermost_wall <= sign * outermost_fluid:
                status[section] = "ambiguous_wall"
                continue
            status[section] = "selected"
            np.equal(side_section, outermost_fluid, out=lining_section)
            np.logical_and(lining_section, fluid_section, out=lining_section)
        lining |= side_lining
    return outputs


def capsule_code(
    coronal: bool, fluid_bright: bool, femur: bool, menisci: bool, wall: bool
) -> str:
    """Name why the outer capsular wall at the side recesses is or is not found."""
    if not coronal:
        return "abstain_not_a_coronal_slice"
    if not fluid_bright:
        return "abstain_fluid_not_bright_on_this_sequence"
    if not femur:
        return "abstain_no_femur"
    if not menisci:
        return "abstain_no_two_menisci_to_locate_the_side_recesses"
    if not wall:
        return "abstain_no_dark_outer_wall_at_the_recesses"
    return "identified"


def retinacular_walls(
    plane: np.ndarray,
    white: np.ndarray,
    labels: np.ndarray,
    peaks: tuple[Peak, ...],
    patella_target: np.ndarray,
    femur_target: np.ndarray,
    basis_lps: np.ndarray,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
    spacing_rc: np.ndarray,
    available: np.ndarray,
    measures: Measures | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    """Measure the outer wall strip beside each bright patellofemoral recess.

    The carried patella and femur are landmarks. Their lens regions are reach targets only:
    the largest white component on each side must come within SHELL_MM of both. The posterior
    interval runs from the patella target's mean position to the strongest existing femoral peak.
    On each native cross-section, the strip lies outboard of the selected white component by at
    most SHELL_MM. Its whole tied minimum signal band is named only when contiguous and darker
    than the adjacent white component. On those same accepted sections, `retinacula_<side>_lining`
    retains the selected fluid component's cavity-facing outboard edge beside that wall. This
    localizes the wall and adjacent cavity surface; it does not measure membrane signal, thickness,
    or full course.
    """
    shape = plane.shape
    names = {
        "positive_inner": (RETINACULA[0], 1.0),
        "negative_inner": (RETINACULA[1], -1.0),
    }
    posterior_axis = int(np.argmax(np.abs(np.asarray(basis_lps)[1, :])))
    section_count = shape[posterior_axis]
    arrays: dict[str, np.ndarray] = {
        object_name: np.zeros(shape, dtype=bool) for object_name, _ in names.values()
    }
    arrays.update(
        {
            "retinacula_white": np.asarray(white, dtype=bool),
            "retinacula_available": np.asarray(available, dtype=bool),
            "retinacula_patella_holder": np.zeros(shape, dtype=bool),
            "retinacula_femur_holder": np.zeros(shape, dtype=bool),
            "retinacula_posterior_interval": np.zeros(shape, dtype=bool),
            "retinacula_femur_peak_rc": np.asarray([-1, -1], dtype=np.int32),
            "retinacula_femur_peak_depth_mm": np.asarray(np.nan),
            "retinacula_back_mm": np.asarray(back_mm, dtype=np.float64),
            "retinacula_inner_mm": np.asarray(inner_mm, dtype=np.float64),
            "retinacula_native_section_axis": np.asarray(posterior_axis, dtype=np.int8),
        }
    )
    arrays["retinacula_posterior_interval_bounds_mm"] = np.asarray(
        [np.nan, np.nan], dtype=np.float64
    )
    for side in names:
        arrays[f"retinacula_{side}_component_labels"] = np.zeros(shape, dtype=np.int32)
        arrays[f"retinacula_{side}_selected_recess"] = np.zeros(shape, dtype=bool)
        arrays[f"retinacula_{side}_lining"] = np.zeros(shape, dtype=bool)
        arrays[f"retinacula_{side}_strip"] = np.zeros(shape, dtype=bool)
        arrays[f"retinacula_{side}_minimum_band"] = np.zeros(shape, dtype=bool)
        arrays[f"retinacula_{side}_row_minimum"] = np.full(
            section_count, np.nan, dtype=np.float64
        )
        arrays[f"retinacula_{side}_adjacent_white_median"] = np.full(
            section_count, np.nan, dtype=np.float64
        )
        arrays[f"retinacula_{side}_row_status"] = np.zeros(section_count, dtype=np.int8)
        arrays[f"retinacula_{side}_tied_minimum_runs"] = np.zeros(
            section_count, dtype=np.int16
        )

    codes: dict[str, str] = {}
    patella_target = np.asarray(patella_target, dtype=bool)
    femur_target = np.asarray(femur_target, dtype=bool)
    patella_holder = region_holding(labels, patella_target)
    femur_holder = region_holding(labels, femur_target)
    arrays["retinacula_patella_holder"] = patella_holder
    arrays["retinacula_femur_holder"] = femur_holder

    prerequisites = ""
    if not patella_target.any():
        prerequisites = "abstain_no_patella_carried"
    elif not femur_target.any():
        prerequisites = "abstain_no_femur_carried"
    elif not patella_holder.any():
        prerequisites = "abstain_no_patellar_region"
    elif not femur_holder.any():
        prerequisites = "abstain_no_femoral_region"

    femur_peak = None
    if not prerequisites:
        femur_peaks = [
            peak
            for peak in peaks
            if 0 <= peak.peak_rc[0] < shape[0]
            and 0 <= peak.peak_rc[1] < shape[1]
            and femur_holder[peak.peak_rc]
        ]
        if femur_peaks:
            femur_peak = max(femur_peaks, key=lambda peak: peak.depth_mm)
            arrays["retinacula_femur_peak_rc"] = np.asarray(
                femur_peak.peak_rc, dtype=np.int32
            )
            arrays["retinacula_femur_peak_depth_mm"] = np.asarray(
                femur_peak.depth_mm, dtype=np.float64
            )
        else:
            prerequisites = "abstain_no_femoral_peak"

    posterior_start = posterior_end = np.nan
    if not prerequisites and femur_peak is not None:
        posterior_start = float(np.asarray(back_mm)[patella_target].mean())
        posterior_end = float(back_mm[femur_peak.peak_rc])
        if posterior_end <= posterior_start:
            prerequisites = "abstain_no_posterior_interval"
        else:
            interval = (back_mm >= posterior_start) & (back_mm <= posterior_end)
            arrays["retinacula_posterior_interval"] = interval
            arrays["retinacula_posterior_interval_bounds_mm"] = np.asarray(
                [posterior_start, posterior_end], dtype=np.float64
            )

    if prerequisites:
        for object_name, _ in names.values():
            codes[object_name] = prerequisites
        return arrays, codes

    midline = float(np.asarray(inner_mm)[patella_target].mean())
    arrays["retinacula_patella_midline_inner_mm"] = np.asarray(midline)
    patella_distance = (
        measures.distance(patella_holder, spacing_rc)
        if measures is not None
        else distance_from(patella_holder, spacing_rc)
    )
    femur_distance = (
        measures.distance(femur_holder, spacing_rc)
        if measures is not None
        else distance_from(femur_holder, spacing_rc)
    )
    arrays["retinacula_patella_holder_distance_mm"] = patella_distance
    arrays["retinacula_femur_holder_distance_mm"] = femur_distance
    valid_white = np.asarray(white, dtype=bool) & np.asarray(available, dtype=bool)
    arrays["retinacula_valid_white"] = valid_white

    for side, (object_name, sign) in names.items():
        side_mask = sign * (inner_mm - midline) > 0.0
        candidate = valid_white & arrays["retinacula_posterior_interval"] & side_mask
        components, component_count = ndi.label(candidate, structure=FOUR_NEIGHBOURS)
        arrays[f"retinacula_{side}_component_labels"] = components.astype(np.int32)
        eligible: list[tuple[int, int]] = []
        for component_id in range(1, component_count + 1):
            component = components == component_id
            reaches_patella = np.any(patella_distance[component] <= SHELL_MM)
            reaches_femur = np.any(femur_distance[component] <= SHELL_MM)
            if reaches_patella and reaches_femur:
                eligible.append((int(component.sum()), component_id))
        if not eligible:
            codes[object_name] = "abstain_no_fluid_recess_at_the_patella"
            continue
        _, selected_id = max(eligible)
        recess = components == selected_id
        arrays[f"retinacula_{side}_selected_recess"] = recess

        def section(values):
            return values if posterior_axis == 0 else values.T

        inner_section = section(inner_mm)
        available_section = section(arrays["retinacula_available"])
        white_section = section(white)
        recess_section = section(recess)
        plane_section = section(plane)
        lining_section = section(arrays[f"retinacula_{side}_lining"])
        strip_section = np.zeros(plane_section.shape, dtype=bool)
        minimum_section = np.zeros(plane_section.shape, dtype=bool)
        minimum_values = arrays[f"retinacula_{side}_row_minimum"]
        white_values = arrays[f"retinacula_{side}_adjacent_white_median"]
        row_status = arrays[f"retinacula_{side}_row_status"]
        tied_runs = arrays[f"retinacula_{side}_tied_minimum_runs"]
        outward_section = sign * (inner_section - midline)
        interval_section = section(arrays["retinacula_posterior_interval"])
        for section_index in range(plane_section.shape[0]):
            recess_across = recess_section[section_index]
            if not recess_across.any():
                continue
            outboard_edge = float(outward_section[section_index, recess_across].max())
            separation = outward_section[section_index] - outboard_edge
            strip = (
                (separation >= 0.0)
                & (separation <= SHELL_MM)
                & interval_section[section_index]
                & available_section[section_index]
                & ~white_section[section_index]
                & (outward_section[section_index] > 0.0)
            )
            strip_section[section_index] = strip
            columns = np.flatnonzero(strip)
            if not columns.size:
                continue
            adjacent = float(np.median(plane_section[section_index, recess_across]))
            minimum = float(np.min(plane_section[section_index, columns]))
            tied = strip & (plane_section[section_index] == minimum)
            tied_columns = np.flatnonzero(tied)
            starts = np.r_[0, np.flatnonzero(np.diff(tied_columns) > 1) + 1]
            run_count = len(starts)
            minimum_values[section_index] = minimum
            white_values[section_index] = adjacent
            tied_runs[section_index] = run_count
            if run_count > 1:
                row_status[section_index] = 2
            elif minimum < adjacent:
                row_status[section_index] = 1
                minimum_section[section_index] = tied
                lining_section[section_index] = recess_across & (
                    outward_section[section_index] == outboard_edge
                )
            else:
                row_status[section_index] = 3

        arrays[f"retinacula_{side}_strip"] = (
            strip_section if posterior_axis == 0 else strip_section.T
        )
        arrays[f"retinacula_{side}_minimum_band"] = (
            minimum_section if posterior_axis == 0 else minimum_section.T
        )
        if minimum_section.any():
            arrays[object_name] = (
                minimum_section if posterior_axis == 0 else minimum_section.T
            )
            codes[object_name] = "identified"
        else:
            codes[object_name] = "abstain_no_outboard_wall_minimum"
    return arrays, codes


def relative_outer_wall(
    plane: np.ndarray,
    body: np.ndarray,
    white: np.ndarray,
    available: np.ndarray,
    outward_mm: np.ndarray,
    section_axis: int,
    width_mm: float = SHELL_MM,
) -> dict[str, np.ndarray]:
    """Read a local low-signal band outside a white body, section by section.

    The outward body edge locates an available, nonwhite strip no farther than ``width_mm``
    away. On each section, the exact acquired minimum is retained only when its tied pixels
    form one contiguous run and are darker than the same-section white body median. This is a
    local relative reading; the strip width is a location allowance, not a measured thickness.

    Status is 0 when the section cannot be read, 1 for one accepted contiguous minimum, 2 for
    separated tied minima, and 3 when the minimum is not darker than the adjacent body median.
    Nonfinite signal or position values are excluded from readings.
    """
    plane_array = np.asarray(plane)
    body_array = np.asarray(body)
    white_array = np.asarray(white)
    available_array = np.asarray(available)
    outward_array = np.asarray(outward_mm)
    arrays = (plane_array, body_array, white_array, available_array, outward_array)
    if any(array.ndim != 2 for array in arrays):
        raise ValueError("plane, masks, and outward_mm must all be two-dimensional")
    if any(array.shape != plane_array.shape for array in arrays[1:]):
        raise ValueError("plane, masks, and outward_mm must have the same shape")
    if any(
        array.dtype != np.dtype(bool)
        for array in (body_array, white_array, available_array)
    ):
        raise ValueError("body, white, and available must be boolean masks")
    if (
        isinstance(section_axis, (bool, np.bool_))
        or not isinstance(section_axis, (int, np.integer))
        or int(section_axis) not in (0, 1)
    ):
        raise ValueError("section_axis must be 0 or 1")
    if isinstance(width_mm, (bool, np.bool_)) or not isinstance(
        width_mm, (int, float, np.integer, np.floating)
    ):
        raise TypeError("width_mm must be a finite nonnegative scalar")
    width = float(width_mm)
    if not np.isfinite(width) or width < 0.0:
        raise ValueError("width_mm must be a finite nonnegative scalar")
    if not np.issubdtype(plane_array.dtype, np.number) or np.issubdtype(
        plane_array.dtype, np.complexfloating
    ):
        raise ValueError("plane must contain real numeric signal values")
    if not np.issubdtype(outward_array.dtype, np.number) or np.issubdtype(
        outward_array.dtype, np.complexfloating
    ):
        raise ValueError("outward_mm must contain real numeric positions")

    axis = int(section_axis)

    def sections(values: np.ndarray) -> np.ndarray:
        return values if axis == 0 else values.T

    signal = sections(plane_array.astype(np.float64, copy=False))
    body_mask = sections(body_array)
    white_mask = sections(white_array)
    available_mask = sections(available_array)
    outward = sections(outward_array.astype(np.float64, copy=False))
    section_count = signal.shape[0]
    native_shape = plane_array.shape
    strip = np.zeros(signal.shape, dtype=bool)
    minimum_band = np.zeros(signal.shape, dtype=bool)
    lining_edge = np.zeros(signal.shape, dtype=bool)
    body_outer_edge = np.full(section_count, np.nan, dtype=np.float64)
    row_minimum = np.full(section_count, np.nan, dtype=np.float64)
    adjacent_median = np.full(section_count, np.nan, dtype=np.float64)
    status = np.zeros(section_count, dtype=np.int8)
    tied_runs = np.zeros(section_count, dtype=np.int16)

    for section_index in range(section_count):
        row_body = (
            body_mask[section_index]
            & white_mask[section_index]
            & available_mask[section_index]
            & np.isfinite(signal[section_index])
            & np.isfinite(outward[section_index])
        )
        if not row_body.any():
            continue
        edge = float(np.max(outward[section_index, row_body]))
        body_outer_edge[section_index] = edge
        separation = outward[section_index] - edge
        row_strip = (
            np.isfinite(outward[section_index])
            & np.isfinite(signal[section_index])
            & (separation >= 0.0)
            & (separation <= width)
            & available_mask[section_index]
            & ~white_mask[section_index]
        )
        strip[section_index] = row_strip
        body_reading = row_body
        if not row_strip.any() or not body_reading.any():
            continue
        minimum = float(np.min(signal[section_index, row_strip]))
        adjacent = float(np.median(signal[section_index, body_reading]))
        tied = row_strip & (signal[section_index] == minimum)
        tied_columns = np.flatnonzero(tied)
        run_starts = np.r_[0, np.flatnonzero(np.diff(tied_columns) > 1) + 1]
        run_count = len(run_starts)
        row_minimum[section_index] = minimum
        adjacent_median[section_index] = adjacent
        tied_runs[section_index] = run_count
        if run_count > 1:
            status[section_index] = 2
        elif minimum < adjacent:
            status[section_index] = 1
            minimum_band[section_index] = tied
            lining_edge[section_index] = row_body & (outward[section_index] == edge)
        else:
            status[section_index] = 3

    if axis == 1:
        strip = strip.T
        minimum_band = minimum_band.T
        lining_edge = lining_edge.T
    return {
        "strip": strip.reshape(native_shape),
        "minimum_band": minimum_band.reshape(native_shape),
        "lining_edge": lining_edge.reshape(native_shape),
        "body_outer_edge_mm": body_outer_edge,
        "row_minimum": row_minimum,
        "adjacent_median": adjacent_median,
        "status": status,
        "tied_runs": tied_runs,
        "section_axis": np.asarray(axis, dtype=np.int8),
    }


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


def relative_signal(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """One acquired nonnegative signal relative to another at the same physical places.
    A zero or unavailable denominator has no ratio, recorded as NaN. Multiplicative changes
    of either acquisition scale the ratios uniformly; additive changes need not."""
    first = np.asarray(numerator, dtype=np.float64)
    second = np.asarray(denominator, dtype=np.float64)
    if first.ndim != 2 or second.shape != first.shape:
        raise ValueError("signals_must_share_a_2d_shape")
    ratio = np.full(first.shape, np.nan)
    valid = np.isfinite(first) & np.isfinite(second) & (first >= 0) & (second > 0)
    with np.errstate(over="ignore"):
        np.divide(first, second, out=ratio, where=valid)
    ratio[~np.isfinite(ratio)] = np.nan
    return handed_on(ratio)


def suprapatellar_pads(
    ratio: np.ndarray,
    combined: np.ndarray,
    basis_lps: np.ndarray,
    back_mm: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Part the named suprapatellar fat about the internal opposed-contrast seam.
    On cross-sections along the leg, the seam is the largest FS/non-FS ratio strictly inside
    the combined fat, with fat on both sides. Flat or separated tied maxima give no seam.
    Contiguous ties retain the whole ridge. No section is interpolated from its neighbours."""
    signal = np.asarray(ratio, dtype=np.float64)
    combined = np.asarray(combined, dtype=bool)
    back = np.asarray(back_mm, dtype=np.float64)
    basis = np.asarray(basis_lps, dtype=np.float64)
    if signal.ndim != 2 or combined.shape != signal.shape or back.shape != signal.shape:
        raise ValueError("pad_readings_must_share_a_2d_shape")
    if basis.shape != (3, 2) or not np.all(np.isfinite(basis)):
        raise ValueError("invalid_lps_basis")
    if not np.all(np.isfinite(back)):
        raise ValueError("invalid_posterior_positions")
    row_axis = abs(basis[2, 0]) >= abs(basis[2, 1])
    mask, posterior = (combined, back) if row_axis else (combined.T, back.T)
    signal = signal if row_axis else signal.T
    anterior, rear, ridge = (np.zeros(mask.shape, dtype=bool) for _ in range(3))
    for row in range(mask.shape[0]):
        ids = np.flatnonzero(mask[row])
        if not len(ids):
            continue
        y = posterior[row, ids]
        inside = (y > y.min()) & (y < y.max()) & np.isfinite(signal[row, ids])
        candidates = ids[inside]
        if not len(candidates):
            continue
        values = signal[row, candidates]
        if np.all(values == values[0]):
            continue
        tied = candidates[values == values.max()]
        if int(tied[-1] - tied[0] + 1) != len(tied):
            continue
        ridge[row, tied] = True
        seam = posterior[row, tied]
        anterior[row, ids[y < seam.min()]] = True
        rear[row, ids[y > seam.max()]] = True
    if not row_axis:
        anterior, rear, ridge = anterior.T, rear.T, ridge.T
    code = (
        "abstain_no_suprapatellar_fat"
        if not combined.any()
        else "identified"
        if ridge.any()
        else "abstain_no_internal_seam"
    )
    return anterior, rear, ridge, code


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


@dataclass(frozen=True, slots=True)
class TendonBodies:
    """The whole dark bodies on one slice and their mean physical positions, read once.
    Position arrays are indexed by the body's label minus one; zero is outside every body."""

    labels: np.ndarray
    back_mm: np.ndarray
    inner_mm: np.ndarray


def dark_tendon_bodies(
    dark: np.ndarray,
    free: np.ndarray,
    spacing_rc: np.ndarray,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
) -> TendonBodies:
    """Close the low signal's one-pixel cracks, keep thick bodies and read their positions.
    This is the semimembranosus selector's existing candidate construction, shared with the
    semitendinosus; it introduces no new thickness or signal level."""
    body = ndi.binary_closing(dark & free, structure=FOUR_NEIGHBOURS) & free
    labels, count = ndi.label(thick_parts(body, spacing_rc, MENISCUS_THICKNESS_MM))
    index = np.arange(1, count + 1)
    back = np.asarray(ndi.mean(back_mm, labels, index=index)) if count else np.empty(0)
    inner = (
        np.asarray(ndi.mean(inner_mm, labels, index=index)) if count else np.empty(0)
    )
    return TendonBodies(handed_on(labels), handed_on(back), handed_on(inner))


def native_dark_bodies(
    dark: np.ndarray,
    free: np.ndarray,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
) -> TendonBodies:
    """The same low signal at the pixel scale, a lens complementary to `dark_tendon_bodies`, for a
    cord thinner than its small-body scale: close cracks by the 3 x 3 square (8 neighbours), keep
    it where `free` (not air, skin or the black margin), rub away the parts too thin to hold a
    4-neighbour cross (under three pixels across; an opening, which also trims a kept body's
    corners), and label 4-connected bodies with their mean positions. Both operations
    are sampling-scale, not anatomical sizes or signal levels. The caller supplies `dark`, `free`
    and the two positions from the slice's shared reading, once; the shared lens is untouched."""
    body = ndi.binary_closing(dark & free, structure=EIGHT_NEIGHBOURS) & free
    labels, count = ndi.label(
        ndi.binary_opening(body, structure=FOUR_NEIGHBOURS), structure=FOUR_NEIGHBOURS
    )
    index = np.arange(1, count + 1)
    back = np.asarray(ndi.mean(back_mm, labels, index=index)) if count else np.empty(0)
    inner = (
        np.asarray(ndi.mean(inner_mm, labels, index=index)) if count else np.empty(0)
    )
    return TendonBodies(handed_on(labels), handed_on(back), handed_on(inner))


def semimembranosus_on_slice(
    bodies: TendonBodies,
    region: np.ndarray,
    condyle: Peak,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The front dark body at the tibia's back-inner corner, reaching the condyle's region.
    `bodies` is this slice's shared dark-body reading, including its one-pixel crack closure
    and existing small-body scale. Its means lie inside and behind the condyle's peak.
    `measures` supplies the shared distance to that region where the run keeps it."""
    none = np.zeros(bodies.labels.shape, dtype=bool)
    count = len(bodies.back_mm)
    if not count:
        return none
    index = np.arange(1, count + 1)
    to_region = (
        distance_from(region, spacing_rc)
        if measures is None
        else measures.distance(region, spacing_rc)
    )
    corner = (
        (bodies.inner_mm > float(inner_mm[condyle.peak_rc]))
        & (bodies.back_mm > float(back_mm[condyle.peak_rc]))
        & (np.asarray(ndi.minimum(to_region, bodies.labels, index=index)) <= SHELL_MM)
    )
    if not corner.any():
        return none
    return bodies.labels == int(index[corner][np.argmin(bodies.back_mm[corner])])


def semitendinosus_on_slice(
    bodies: TendonBodies,
    semimembranosus: np.ndarray,
    condyle: Peak | None,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> tuple[np.ndarray, str]:
    """The separate whole dark body behind the semimembranosus, nearest it on the inner side.
    Shared body means, the named tendon and the condyle locate it; no slice coordinates,
    component IDs or new numerical cutoff select it."""
    none = np.zeros(bodies.labels.shape, dtype=bool)
    if not semimembranosus.any():
        return none, "abstain_no_semimembranosus_reference"
    if condyle is None:
        return none, "abstain_no_inner_condyle_peak"
    count = len(bodies.back_mm)
    if not count:
        return none, "abstain_no_dark_body_candidates"
    index = np.arange(1, count + 1)
    eligible = index[
        (bodies.inner_mm > float(inner_mm[condyle.peak_rc]))
        & (bodies.back_mm > float(back_mm[semimembranosus].max()))
    ]
    if not eligible.size:
        return none, "abstain_no_body_meets_both_spatial_relations"
    to_tendon = (
        distance_from(semimembranosus, spacing_rc)
        if measures is None
        else measures.distance(semimembranosus, spacing_rc)
    )
    distances = np.asarray(ndi.minimum(to_tendon, bodies.labels, index=eligible))
    nearest = np.flatnonzero(distances == distances.min())
    if len(nearest) != 1:
        return none, "abstain_tied_nearest_bodies"
    return bodies.labels == int(eligible[nearest[0]]), "identified"


def gracilis_on_slice(
    bodies: TendonBodies,
    semimembranosus: np.ndarray,
    semitendinosus: np.ndarray,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
    spacing_rc: np.ndarray,
    knee: str,
    measures: Measures | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
    """The separate whole dark body (`bodies`, from `native_dark_bodies`) on the knee's inner side
    of both named tendons and in front of the semitendinosus, overlapping neither, nearest the
    pair in physical distance. `back_mm` and `inner_mm` are the slice's positions (`inner_mm`
    toward the knee's inner side, which `knee`, the header's "R" or "L", names); `measures` supply
    the distance to the pair where the run keeps them. An exact nearest tie abstains.

    Returns the mask, the readings made (a reading is present only once the rule reached it; all
    ndarrays: `native_body_labels`, `native_body_inner_mm`, `native_body_back_mm`, `eligible_ids`
    and `eligible_distance_mm`, the latter two in the same order) and the code."""
    none = np.zeros(bodies.labels.shape, dtype=bool)
    readings: dict[str, np.ndarray] = {}
    if knee not in ("R", "L"):
        return none, readings, "abstain_header_names_no_knee"
    if not semimembranosus.any():
        return none, readings, "abstain_no_semimembranosus_reference"
    if not semitendinosus.any():
        return none, readings, "abstain_no_semitendinosus_reference"
    count = len(bodies.back_mm)
    if not count:
        return none, readings, "abstain_no_native_dark_body"
    readings.update(
        native_body_labels=bodies.labels,
        native_body_inner_mm=bodies.inner_mm,
        native_body_back_mm=bodies.back_mm,
    )
    index = np.arange(1, count + 1)
    pair = semimembranosus | semitendinosus
    touches = np.bincount(bodies.labels[pair], minlength=count + 1)[1:] > 0
    eligible = index[
        ~touches
        & (
            bodies.inner_mm
            > max(
                float(inner_mm[semimembranosus].mean()),
                float(inner_mm[semitendinosus].mean()),
            )
        )
        & (bodies.back_mm < float(back_mm[semitendinosus].mean()))
    ]
    readings["eligible_ids"] = eligible.astype(np.int32)
    if not eligible.size:
        return (
            none,
            readings,
            "abstain_no_body_medial_to_both_and_in_front_of_the_semitendinosus",
        )
    to_pair = (
        distance_from(pair, spacing_rc)
        if measures is None
        else measures.distance(pair, spacing_rc)
    )
    distances = np.asarray(ndi.minimum(to_pair, bodies.labels, index=eligible))
    readings["eligible_distance_mm"] = distances
    nearest = np.flatnonzero(distances == distances.min())
    if len(nearest) != 1:
        return none, readings, "abstain_tied_nearest_bodies"
    return bodies.labels == int(eligible[nearest[0]]), readings, "identified"


def window_pixels(spacing_rc: np.ndarray, length_mm: float) -> tuple[int, int]:
    """The odd window (rows, columns) in pixels that covers `length_mm` physically on each axis, from
    the slice's own pixel pitch (the nearest whole count, made odd so a pixel is its centre)."""
    steps = np.asarray(spacing_rc, dtype=np.float64)
    if steps.shape != (2,) or not np.all(np.isfinite(steps)) or np.any(steps <= 0):
        raise ValueError("invalid_spacing")
    counts = np.rint(length_mm / steps).astype(int)
    rows, cols = (int(n + 1 if n % 2 == 0 else n) for n in counts)
    return rows, cols


def local_lightness(
    plane: np.ndarray, excluded: np.ndarray, spacing_rc: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Each place's light against its surroundings, in the slice's own millimetres: the plane after
    a `SAMPLING_PIXELS` median of seen, non-low samples (`smooth`), over the median of the seen light of the window
    `LOCAL_CONTRAST_MM` across on each axis round it (`surround`).

    `excluded` are the places with no reading: the low signal, what is not finite and the black
    margin. They have none (NaN), never a dark one, in `smooth`, in every surround and in the
    ratio; places outside the picture are unseen too. A surround that holds nothing seen, or whose
    median is zero, gives NaN, not a ratio. Returns (lightness, smooth, surround), float arrays of
    the plane's shape."""
    from knee.objects.local_lightness import local_lightness_jit

    values = np.asarray(plane, dtype=np.float64)
    hidden = np.asarray(excluded, dtype=bool)
    if values.ndim != 2 or hidden.shape != values.shape:
        raise ValueError("lightness_inputs_must_share_a_2d_shape")
    return local_lightness_jit(
        values, hidden, window_pixels(spacing_rc, LOCAL_CONTRAST_MM)
    )


def muscle_grey_bodies(lightness: np.ndarray) -> np.ndarray:
    """The whole 8-connected bodies of muscle-grey light: the places whose relative lightness lies
    in `MUSCLE_GREY` (the lower bound up to, not including, the upper), after an opening by a
    `SAMPLING_PIXELS` square that rubs away what is narrower than the sampling lens. Each body its
    own label, 0 elsewhere; no reading (NaN) is never grey."""
    low, high = MUSCLE_GREY
    with np.errstate(invalid="ignore"):
        grey = (lightness >= low) & (lightness < high)
    body = ndi.binary_opening(grey, structure=np.ones((SAMPLING_PIXELS,) * 2, bool))
    labels, _ = ndi.label(body, structure=EIGHT_NEIGHBOURS)
    return np.asarray(labels, dtype=np.int32)


SARTORIUS_SCOPE_STATUSES = ("present", "window_clipped_to_image")


def sartorius_scope_window(
    scope: dict | None, shape: tuple[int, int]
) -> tuple[int, int, int, int] | None:
    """Return validated exclusive RC bounds, rejecting malformed values without coercion."""
    if (
        not isinstance(scope, dict)
        or scope.get("status") not in SARTORIUS_SCOPE_STATUSES
    ):
        return None
    if len(shape) != 2 or any(
        isinstance(n, (bool, np.bool_))
        or not isinstance(n, (int, np.integer))
        or n <= 0
        for n in shape
    ):
        return None
    try:
        raw_values = scope["window_rc_exclusive"]
        if any(isinstance(v, (bool, np.bool_)) for v in raw_values):
            return None
        raw = np.asarray(raw_values)
    except (KeyError, TypeError, ValueError):
        return None
    if raw.shape != (4,) or raw.dtype.kind not in "iuf" or not np.all(np.isfinite(raw)):
        return None
    if np.any(raw != np.floor(raw)):
        return None
    r0, r1, c0, c1 = (int(v) for v in raw)
    if not (0 <= r0 < r1 <= shape[0] and 0 <= c0 < c1 <= shape[1]):
        return None
    return r0, r1, c0, c1


def scoped_local_lightness(
    plane: np.ndarray,
    excluded: np.ndarray,
    spacing_rc: np.ndarray,
    window: tuple[int, int, int, int],
    available: np.ndarray | None = None,
    not_low: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Compute a query window with its required contrast context and retain both domains.

    Context values are the complete crop actually passed to the existing contrast measurement.
    Query outputs contain values only inside the requested window; exterior pixels are unqueried.
    Queried pixels excluded for availability, low signal, or nonfinite input remain unavailable.
    """
    values = np.asarray(plane, dtype=np.float64)
    hidden = np.asarray(excluded, dtype=bool)
    available_mask = ~hidden if available is None else np.asarray(available, dtype=bool)
    not_low_mask = ~hidden if not_low is None else np.asarray(not_low, dtype=bool)
    if (
        values.ndim != 2
        or hidden.shape != values.shape
        or available_mask.shape != values.shape
        or not_low_mask.shape != values.shape
    ):
        raise ValueError("lightness_inputs_must_share_a_2d_shape")
    r0, r1, c0, c1 = window
    rows, cols = window_pixels(spacing_rc, LOCAL_CONTRAST_MM)
    halo_r = rows // 2 + SAMPLING_PIXELS // 2
    halo_c = cols // 2 + SAMPLING_PIXELS // 2
    cr0, cr1 = max(0, r0 - halo_r), min(values.shape[0], r1 + halo_r)
    cc0, cc1 = max(0, c0 - halo_c), min(values.shape[1], c1 + halo_c)
    context_raw = values[cr0:cr1, cc0:cc1]
    context_hidden = hidden[cr0:cr1, cc0:cc1]
    context_available = available_mask[cr0:cr1, cc0:cc1]
    context_not_low = not_low_mask[cr0:cr1, cc0:cc1]
    context_finite = np.isfinite(context_raw)
    sub = local_lightness(context_raw, context_hidden, spacing_rc)
    inner = (slice(r0 - cr0, r1 - cr0), slice(c0 - cc0, c1 - cc0))
    query_values = []
    for part in sub:
        full = np.full(values.shape, np.nan, dtype=np.float64)
        full[r0:r1, c0:c1] = np.asarray(part)[inner]
        query_values.append(full)
    queried = np.zeros(values.shape, dtype=bool)
    queried[r0:r1, c0:c1] = True
    effective_context = (
        context_available & context_not_low & context_finite & ~context_hidden
    )
    effective_query = np.zeros(values.shape, dtype=bool)
    effective_query[r0:r1, c0:c1] = effective_context[inner]
    return {
        "lightness": query_values[0],
        "smooth": query_values[1],
        "surround": query_values[2],
        "query_window": queried,
        "effective_available": effective_query,
        "context_raw": context_raw.copy(),
        "context_excluded": context_hidden.copy(),
        "context_available": context_available.copy(),
        "context_not_low": context_not_low.copy(),
        "context_finite": context_finite,
        "context_effective_available": effective_context,
        "context_lightness": np.asarray(sub[0]),
        "context_smooth": np.asarray(sub[1]),
        "context_surround": np.asarray(sub[2]),
        "window": np.asarray([r0, r1, c0, c1], dtype=np.int32),
        "context": np.asarray([cr0, cr1, cc0, cc1], dtype=np.int32),
        "halo": np.asarray([halo_r, halo_c], dtype=np.int32),
    }


def sartorius_on_slice(
    plane: np.ndarray,
    low: np.ndarray,
    unseen: np.ndarray,
    gracilis_lps: np.ndarray,
    frame: PlaneFrame,
    knee: str,
    measures: Measures | None = None,
    target: np.ndarray | None = None,
    scope: dict | None = None,
    available: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
    """The sartorius on a fat-suppressed axial slice (its paragraph in the module note): of the
    muscle-grey bodies (`muscle_grey_bodies` of `local_lightness`), the largest whole one on the
    knee's inner side of the gracilis's places and in front of them, reaching within
    `GRACILIS_REACH_MM` of them. Two of exactly the largest size abstain.

    `gracilis_lps` are the gracilis's places in the scanner's millimetres, from the slice it was
    named on, and `frame` is this slice's: they are projected along its normal
    (`projected_places`) into a target, however far off its plane they lie, unless the caller
    already did so and hands that `target` (a boolean mask of the plane's shape) in. `low` is the
    lens's low signal and `unseen` what has no light here (not available, or the black margin);
    `knee` is the header's "R" or "L", which names the inner side. `measures` are the slice's
    shared measures, when its caller keeps them.

    `scope` is the caller's source window (`source_window` result around the target, sized from
    the sartorius's authored extent plus `GRACILIS_REACH_MM`). When given, the contrast is
    computed only over that window plus the context its interior needs
    (`scoped_local_lightness`); everything else is unmeasured (NaN lightness, `contrast_measured`
    False), the grey-body rule is applied unchanged within the window, and a scope that cannot be
    read refuses with `abstain_sartorius_scope_unavailable`. Without a scope the whole plane is
    measured as before.

    Returns the full-frame mask, every reading actually made (arrays only, present once the rule
    reached it: the target, its source's separation from the plane, the scope address, offset,
    dimensions and context, the window, `smooth`, `surround`, `lightness`, the labelled bodies
    with their inner and back means, sizes and status (`SARTORIUS_BODY_STATUS`), the target's
    distance, and the eligible bodies with their reach) and the code."""
    values = np.asarray(plane, dtype=np.float64)
    low_mask = np.asarray(low, dtype=bool)
    unseen_mask = np.asarray(unseen, dtype=bool)
    available_mask = (
        np.ones(values.shape, dtype=bool)
        if available is None
        else np.asarray(available, dtype=bool)
    )
    finite_input = np.isfinite(values)
    gone = low_mask | unseen_mask | ~available_mask | ~finite_input
    if values.ndim != 2 or any(
        mask.shape != values.shape
        for mask in (gone, low_mask, unseen_mask, available_mask)
    ):
        raise ValueError("sartorius_inputs_must_share_a_2d_shape")
    empty = np.zeros(values.shape, dtype=bool)
    readings: dict[str, np.ndarray] = {}

    def refuse(code: str) -> tuple[np.ndarray, dict[str, np.ndarray], str]:
        return empty, readings, code

    if knee not in ("R", "L"):
        return refuse("abstain_header_names_no_knee")
    places = np.asarray(gracilis_lps, dtype=np.float64)
    if places.size == 0:
        return refuse("abstain_no_gracilis_source")
    if target is None:
        target = projected_places(places, frame, values.shape)
    else:
        target = np.asarray(target, dtype=bool)
        if target.shape != values.shape:
            raise ValueError("sartorius_target_must_share_the_plane_shape")
    readings["gracilis_source_lps"] = places
    readings["gracilis_target"] = target
    readings["gracilis_source_separation_mm"] = np.asarray(
        abs(float((places.mean(axis=0) - frame.origin_lps) @ frame.normal()))
    )
    if not target.any():
        return refuse("abstain_gracilis_projects_outside_the_picture")

    spacing_rc = np.asarray(frame.spacing_rc, dtype=np.float64)
    window = None
    if scope is not None:
        window = sartorius_scope_window(scope, values.shape)
        if window is None:
            return refuse("abstain_sartorius_scope_unavailable")
        readings["contrast_scope_window_rc"] = np.asarray(window, dtype=np.int32)
        readings["contrast_scope_offset_rc"] = np.asarray(window[::2], dtype=np.int32)
        readings["contrast_scope_shape_rc"] = np.asarray(
            [window[1] - window[0], window[3] - window[2]], dtype=np.int32
        )
        readings["contrast_scope_clipped"] = np.asarray(
            bool(scope.get("window_clipped_to_image", False))
        )
        if "projected_half_span_pixels_rc" in scope:
            readings["contrast_scope_half_span_pixels_rc"] = np.asarray(
                scope["projected_half_span_pixels_rc"], dtype=np.float64
            )
        if "target_bbox_rc_exclusive" in scope:
            readings["contrast_scope_target_bbox_rc"] = np.asarray(
                scope["target_bbox_rc_exclusive"], dtype=np.int32
            )
        scoped = scoped_local_lightness(
            values, gone, spacing_rc, window, available_mask, ~low_mask
        )
        lightness, smooth, surround = (
            scoped["lightness"],
            scoped["smooth"],
            scoped["surround"],
        )
        readings.update(
            contrast_query_window=scoped["query_window"],
            contrast_effective_available=scoped["effective_available"],
            contrast_context_rc=scoped["context"],
            contrast_halo_pixels_rc=scoped["halo"],
            contrast_context_raw=scoped["context_raw"],
            contrast_context_excluded=scoped["context_excluded"],
            contrast_context_available=scoped["context_available"],
            contrast_context_not_low=scoped["context_not_low"],
            contrast_context_finite=scoped["context_finite"],
            contrast_context_effective_available=scoped["context_effective_available"],
            contrast_context_lightness=scoped["context_lightness"],
            contrast_context_smooth=scoped["context_smooth"],
            contrast_context_surround=scoped["context_surround"],
        )
    else:
        lightness, smooth, surround = local_lightness(values, gone, spacing_rc)
    readings.update(
        contrast_actual_available=available_mask,
        contrast_not_low=~low_mask,
        contrast_input_finite=finite_input,
        contrast_finite=finite_input & np.isfinite(lightness),
        surround_window_pixels=np.asarray(
            window_pixels(spacing_rc, LOCAL_CONTRAST_MM), dtype=np.int32
        ),
        smooth=smooth,
        surround=surround,
        lightness=lightness,
    )
    if not np.isfinite(lightness).any():
        return refuse("abstain_no_local_contrast")
    labels = muscle_grey_bodies(lightness)
    readings["grey_bodies"] = labels
    count = int(labels.max())
    if not count:
        return refuse("abstain_no_soft_tissue_grey_body")

    basis = frame.basis_lps
    left = (
        positions_along(values.shape, basis, 0)
        if measures is None
        else measures.along(0)
    )
    back = (
        positions_along(values.shape, basis, 1)
        if measures is None
        else measures.along(1)
    )
    inner = left if knee == "R" else -left  # toward the other knee
    index = np.arange(1, count + 1)
    body_inner = np.asarray(ndi.mean(inner, labels, index=index))
    body_back = np.asarray(ndi.mean(back, labels, index=index))
    size = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    status = np.zeros(count, dtype=np.int8)
    readings.update(
        body_inner_mm=body_inner,
        body_back_mm=body_back,
        body_size_pixels=size,
        body_status=status,
    )
    eligible = index[
        (body_inner > float(inner[target].mean()))
        & (body_back < float(back[target].mean()))
    ]
    readings["eligible_ids"] = eligible.astype(np.int32)
    if not eligible.size:
        return refuse(
            "abstain_no_grey_body_medial_to_and_in_front_of_the_gracilis_target"
        )
    to_target = (
        distance_from(target, spacing_rc)
        if measures is None
        else measures.distance(target, spacing_rc)
    )
    reach = np.asarray(ndi.minimum(to_target, labels, index=eligible))
    readings.update(target_distance_mm=to_target, eligible_reach_mm=reach)
    status[eligible - 1] = SARTORIUS_BODY_STATUS["beyond_reach"]
    near = eligible[reach <= GRACILIS_REACH_MM]
    status[near - 1] = SARTORIUS_BODY_STATUS["within_reach"]
    if not near.size:
        return refuse("abstain_no_grey_body_within_reach_of_the_gracilis_target")
    chosen = unique_largest(size[near - 1])
    if chosen is None:
        return refuse("abstain_tied_largest_bodies")
    status[near[chosen] - 1] = SARTORIUS_BODY_STATUS["selected"]
    return labels == int(near[chosen]), readings, "identified"


def bursa_on_slice(
    white: np.ndarray,
    tendon: np.ndarray,
    posterior_region: np.ndarray,
    back_mm: np.ndarray,
    inner_mm: np.ndarray,
    spacing_rc: np.ndarray,
    measures: Measures | None = None,
) -> np.ndarray:
    """The fluid-filled gastrocnemius-semimembranosus bursa at the back-inner knee.

    The tendon locates its anterior end; the region behind the inner condyle locates the
    posterior soft-tissue field. Among connected white bodies on the inner side, behind the
    tendon and before that field's middle, take the largest reaching that field. This uses a
    broad territory as a target, not as an exact muscle mask. A narrow neck need not itself
    be white or reach the tendon on this one slice. No diagnosis is made.
    """
    empty = np.zeros(white.shape, dtype=bool)
    if not (tendon.any() and posterior_region.any() and white.any()):
        return empty
    front = float(np.median(back_mm[tendon]))
    back = float(np.median(back_mm[posterior_region]))
    to_region = (
        distance_from(posterior_region, spacing_rc)
        if measures is None
        else measures.distance(posterior_region, spacing_rc)
    )
    pieces, count = ndi.label(white, structure=np.ones((3, 3), dtype=bool))
    candidates = []
    for region in range(1, count + 1):
        body = pieces == region
        if not front < np.median(back_mm[body]) < back:
            continue
        if np.median(inner_mm[body]) <= 0:
            continue
        if to_region[body].min() <= SHELL_MM:
            candidates.append((int(body.sum()), region))
    return empty if not candidates else pieces == max(candidates)[1]


def bursa_code(
    fluid_bright: bool, tendon: bool, posterior_region: bool, body: bool
) -> str:
    """Why a fluid-filled bursal body is or is not resolved on the tendon's slice."""
    if not fluid_bright:
        return "abstain_fluid_not_bright_on_this_sequence"
    if not tendon:
        return "abstain_no_semimembranosus_tendon"
    if not posterior_region:
        return "abstain_no_region_behind_the_inner_condyle"
    if not body:
        return "abstain_no_fluid_body_in_the_bursal_place"
    return "identified"


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


def fibula_corridor(
    centres_lps: np.ndarray,
    tibia_top_mm: float,
    tibia_middle_lps: np.ndarray,
    knee: str,
) -> np.ndarray:
    """The squint tiles of the fibula's corridor: `fibula_block` (below the tibia's top, on the knee's
    outer side of the tibia's middle) and behind the tibia's middle, where the fibula's description
    puts its middle (`fibula_on_slice`). Positions are the tiles' centres in the scanner's
    millimetres, y toward the back; a tile with no centre is not in it. Empty when the header names
    no knee."""
    block = fibula_block(centres_lps, tibia_top_mm, tibia_middle_lps, knee)
    behind = np.asarray(centres_lps)[..., 1] > float(tibia_middle_lps[1])
    return block & behind


@dataclass(frozen=True, slots=True)
class FibulaPointer:
    """What one slice's cheap reading says of the fibula (`fibula_pointer`): its status
    (`FIBULA_POINTER_STATUS`), the area of the largest whole body that could be the fibula in square
    millimetres (0.0 only where a body was measured absent, NaN where nothing can be said), that
    body's middle in the scanner's millimetres (NaN where there is none), the body and the tibia's
    reference body on the block grid, and how many bodies could be the fibula."""

    status: int
    area_mm2: float
    centroid_lps: np.ndarray
    body: np.ndarray
    tibia: np.ndarray
    candidates: int


def fibula_pointer(
    median: np.ndarray,
    cell_mm: np.ndarray,
    centres_lps: np.ndarray,
    tibia_cells: np.ndarray,
    tibia_middle_cells: np.ndarray,
    light: float,
    tibia_top_mm: float,
    tibia_middle_lps: np.ndarray,
    knee: str,
    cut: np.ndarray,
) -> FibulaPointer:
    """Where one slice's finer cheap reading (`knee.collapse.profile.block_medians` over the
    corridor's window) holds a body that could be the fibula: a pointer, never the fibula itself,
    which `fibula_on_slice` decides on the lens where this points.

    The fibula's description read on blocks, with the tibia's own relations: blocks whose median
    is as bright as the tibia's marrow (within `LIKE_THE_TIBIA` of `light`), with every part
    thinner than `BONE_MM` rubbed away (`thick_parts`, so a bone and not a skin-fat layer); the
    tibia's reference body is the one holding most of `tibia_cells`, the blocks holding the tibia's
    places carried from the middle slice, and it is the tibia only where it also holds the tibia's
    middle (`tibia_middle_cells`, the block holding the middle slice's deepest tibia peak): the
    tibia's two anchors on the slice agree. Beyond the tibia's lateral edge they do not, the
    carried places then lying on whatever bone is under them, and a body cannot be told from the
    tibia there: that is unknown, not absent. Every other body whose middle lies behind the
    tibia's middle, on the knee's outer side of it and at least `FIBULA_BELOW_MM` below the
    tibia's top could be the fibula. `cut` marks the blocks on the window's border where it is not the picture's
    own edge: a body there is not a whole object in view, as in `fibula_on_slice`, and is not read as
    the fibula or as its absence.

    Statuses: `body` (the largest whole candidate's area, its middle, and the count); `none`
    (bodies were read and none could be the fibula: measured absent, area 0.0); `cut` (a candidate
    reaches the window's cut border and no whole one exists: unknown, NaN); `unreadable` (the light
    is not positive, or the tibia's anchors do not agree on one body here, so nothing can be told
    from the tibia: unknown, NaN). Unseen blocks (NaN) are never marrow-like and never dark; they only
    cannot be part of a body.
    """
    values = np.asarray(median, dtype=np.float64)
    nowhere = np.zeros(values.shape, dtype=bool)
    unknown = np.full(3, np.nan)

    def pointer(status: int, area: float = np.nan, found: int = 0) -> FibulaPointer:
        return FibulaPointer(status, area, unknown, nowhere, nowhere, found)

    if not (np.isfinite(light) and light > 0):
        return pointer(FIBULA_POINTER_STATUS["unreadable"])
    low, high = LIKE_THE_TIBIA
    like = np.isfinite(values) & (values >= low * light) & (values <= high * light)
    bodies, count = ndi.label(thick_parts(like, np.asarray(cell_mm), BONE_MM))
    held = bodies[np.asarray(tibia_cells, dtype=bool) & (bodies > 0)]
    middle_held = bodies[np.asarray(tibia_middle_cells, dtype=bool) & (bodies > 0)]
    if not held.size or not middle_held.size:
        return pointer(FIBULA_POINTER_STATUS["unreadable"])
    tibia = int(np.argmax(np.bincount(held)))
    if tibia != int(np.argmax(np.bincount(middle_held))):
        return pointer(FIBULA_POINTER_STATUS["unreadable"])
    cell_area = float(cell_mm[0]) * float(cell_mm[1])
    centres = np.asarray(centres_lps, dtype=np.float64)
    whole, clipped = [], 0
    for body in range(1, count + 1):
        if body == tibia:
            continue
        places = bodies == body
        middle = centres[places].mean(axis=0)
        outer = (
            middle[0] < tibia_middle_lps[0]
            if knee == "R"
            else middle[0] > tibia_middle_lps[0]
        )
        below = tibia_top_mm - middle[2] >= FIBULA_BELOW_MM
        behind = middle[1] > tibia_middle_lps[1]
        if not (outer and below and behind):
            continue
        if (places & np.asarray(cut, dtype=bool)).any():
            clipped += 1
            continue
        whole.append((float(np.count_nonzero(places)) * cell_area, body, middle))
    if not whole:
        status = "cut" if clipped else "none"
        return FibulaPointer(
            FIBULA_POINTER_STATUS[status],
            np.nan if clipped else 0.0,
            unknown,
            nowhere,
            bodies == tibia,
            clipped,
        )
    area, body, middle = max(whole, key=lambda found: found[0])
    return FibulaPointer(
        FIBULA_POINTER_STATUS["body"],
        area,
        middle,
        bodies == body,
        bodies == tibia,
        len(whole) + clipped,
    )


def thick_parts(
    mask: np.ndarray, spacing_rc: np.ndarray, thickness_mm: float
) -> np.ndarray:
    """`mask` with every part thinner than `thickness_mm` rubbed away (an opening by a disc)."""
    radius = thickness_mm / 2.0
    half = np.maximum(1, np.floor(radius / spacing_rc)).astype(int)
    rows, cols = np.mgrid[-half[0] : half[0] + 1, -half[1] : half[1] + 1]
    disc = (rows * spacing_rc[0]) ** 2 + (cols * spacing_rc[1]) ** 2 <= radius**2
    return ndi.binary_opening(mask, structure=disc)


def enclosed_darkness(plane: np.ndarray) -> np.ndarray:
    """Depth of dark closed interiors below their brighter enclosure, measured by erosion
    reconstruction from the native image border. No grey-level cutoff is applied."""
    values = np.asarray(plane, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("plane_must_be_2d")
    if not np.all(np.isfinite(values)):
        raise ValueError("plane_must_be_finite")
    if values.size == 0:
        return np.zeros(values.shape, dtype=np.float64)
    seed = np.full(values.shape, float(np.max(values)), dtype=np.float64)
    seed[0, :] = values[0, :]
    seed[-1, :] = values[-1, :]
    seed[:, 0] = values[:, 0]
    seed[:, -1] = values[:, -1]
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            module=r"skimage\.morphology\.grayreconstruct",
        )
        enclosure = reconstruction(
            seed, values, method="erosion", footprint=np.ones((3, 3), dtype=bool)
        )
    return np.asarray(enclosure - values, dtype=np.float64)


def popliteal_lumens(
    depth: np.ndarray,
    corridor: np.ndarray,
    back_mm: np.ndarray,
    spacing_rc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Select the two strongest complete, thick-body-supported closed lumens in the corridor;
    the one farther forward is the artery and the other the vein. Component labels retain all
    positive enclosed-darkness readings, including components not selected as vessels."""
    depth = np.asarray(depth, dtype=np.float64)
    back = np.asarray(back_mm, dtype=np.float64)
    corridor = np.asarray(corridor, dtype=bool)
    spacing = np.asarray(spacing_rc, dtype=np.float64)
    if depth.ndim != 2 or corridor.shape != depth.shape or back.shape != depth.shape:
        raise ValueError("vessel_inputs_must_share_a_2d_shape")
    if not np.all(np.isfinite(depth)) or not np.all(np.isfinite(back)):
        raise ValueError("vessel_inputs_must_be_finite")
    if (
        spacing.shape != (2,)
        or not np.all(np.isfinite(spacing))
        or np.any(spacing <= 0)
    ):
        raise ValueError("invalid_spacing")
    empty = np.zeros(depth.shape, dtype=bool)
    labels, _ = ndi.label(depth > 0, structure=np.ones((3, 3), dtype=bool))
    labels = np.asarray(labels, dtype=np.int32)
    body = thick_parts(depth > 0, spacing, VESSEL_BODY_MM)
    touched = np.unique(labels[body])
    # a lumen with any place outside the corridor is not wholly in it: one pass finds them all, so
    # no other lumen's places are gathered only to be set aside
    outside = set(np.unique(labels[~corridor]).tolist())
    candidates = []
    means = {}
    anterior_positions = {}
    for label in touched:
        component_id = int(label)
        if component_id == 0 or component_id in outside:
            continue
        component = labels == component_id
        means[component_id] = float(depth[component].mean())
        anterior_positions[component_id] = float(back[component].mean())
        candidates.append(component_id)
    if len(candidates) < 2:
        return empty, empty.copy(), labels, "abstain_no_lumen_pair"
    strongest = sorted(candidates, key=lambda item: (-means[item], item))[:2]
    first, second = strongest
    if anterior_positions[first] == anterior_positions[second]:
        return empty, empty.copy(), labels, "abstain_ambiguous_vessel_order"
    artery_id, vein_id = sorted(strongest, key=lambda item: anterior_positions[item])
    return labels == artery_id, labels == vein_id, labels, "identified"


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
    reading: InteriorRegions,
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
    reading: InteriorRegions,
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
    codes["joint_capsule"] = "not_named_on_this_slice"
    codes["gastrocnemius_semimembranosus_bursa"] = (
        "abstain_requires_the_semimembranosus_slice"
    )
    codes["popliteal_artery"] = codes["popliteal_vein"] = "not_named_on_this_slice"
    codes["semitendinosus"] = "abstain_requires_the_semimembranosus_slice"
    codes["quadriceps_fat_pad"] = codes["prefemoral_fat_pad"] = (
        "not_named_on_this_slice"
    )
    codes["patellar_retinacula"] = "abstain_requires_the_patellar_slice"
    for name in RETINACULA:
        codes[name] = "abstain_requires_the_patellar_slice"
    codes["popliteus_tendon"] = "abstain_requires_the_lcl_slice"
    # The ITB is read from the parts this naming has just made (`iliotibial_band_on_slice`), by the
    # stage after it, which replaces this code with its own.
    codes["iliotibial_band"] = "abstain_requires_the_itb_reading"
    # The biceps tendon is read on a slice of its own, lateral to the fibular head.
    codes["biceps_femoris_tendon"] = "abstain_requires_the_biceps_slice"
    # The gracilis is read on the semimembranosus tendon's slice, from the two hamstring tendons.
    codes["gracilis"] = "abstain_requires_the_semimembranosus_slice"
    # The sartorius is read on the middle axial from the gracilis's physical places, by the stage
    # after the semimembranosus group (`name_sartorius`), which replaces this code with its own.
    codes["sartorius"] = "abstain_requires_the_gracilis_source"
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
