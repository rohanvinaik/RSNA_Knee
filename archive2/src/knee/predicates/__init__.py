"""THE PREDICATES: the twelve findings, each a statement about one named subject.

The knee's own stage. Its warrant is the founder, 2026-10-11:

    "A fracture isn't some vague line-y thing you look for in a whole study/image--it's a break in
    the structural coherence of a 'bone' object. Each of these conditions is, again, almost
    *absurdly* simple once you frame this as an object-centered reasoning task"

    "diagnosis of physical ailments from scan data is *literally* object-oriented reasoning ... the
    mapping to diagnoses here isn't just statistics, it's *literally* recapitulating the exact
    process that a doctor/radiologist would *themselves* be using for THEIR diagnosis"

So a finding is a PREDICATE VIOLATION on an object, a relation, a span or the envelope -- never a
pattern found in a field. A measurement whose scope is the whole image is refused as a predicate.

    Fracture          a bone            break in structural coherence of outline/interior
    Contusion         a bone            interior (marrow) signal anomaly
    Medial OA         femur-tibia med.  cartilage thickness loss; osteophyte; subchondral change
    Lateral OA        femur-tibia lat.  the same, laterally
    PF OA             femur-patella     the same
    Medial Meniscus   its content       continuity
    Lateral Meniscus  its content       continuity
    ACL               notch content     continuity and course
    MCL               medial span       continuity
    Effusion          the cavity        over-fill of its volume
    Synovitis         the lining        excess thickness
    Baker's           the bursa         distension, by its neck between the muscle and the tendon

An unresolved subject ABSTAINS with a named code and is never a negative (law 3). Every bar a
predicate reads is a recorded argument, written down before the run that judges it, and no bar is
ever chosen to separate the gold labels (law 4).

Two limits are recorded rather than engineered around, both established 2026-10-11:

  - the predicates above are stated at the grain the design has settled; the finer forms each one
    needs (a meniscal tear is intrasubstance signal reaching an articular surface on two adjacent
    slices, which is natively a concurrence; an MCL grade 1 preserves continuity) are the founder's
    to teach as the subjects become resolvable;
  - SYNOVITIS is the one finding where going finer stops helping. Its distinguishing property is
    enhancement (an agent the routine acquisition does not contain) or thickness (below one voxel in
    a normal knee). The decomposition stays correct as a description -- recess, fluid and lining are
    three objects -- but the predicate on the third is undecidable in the typical study, and it must
    say UNKNOWN there rather than no.

Record: docs/OBJECT_MODEL.md; openspec/changes/knee-object-model/specs/finding-predicates/spec.md.
State: not built.
"""
