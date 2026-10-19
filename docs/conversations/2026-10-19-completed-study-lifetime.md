# Completed-study lifetime — Rohan, 2026-10-19

Verbatim direct instruction during the production build:

> Also, for the actual competition mode build, seems trivial to address memory concerns by finishing one study completely, reporting what we need to report, then simply dumping the completed run before starting the next one. Or I suppose we can do parallel processing, so we keep however many studies’ data we’re running and dump each when it finishes

Rohan then clarified the output boundary, verbatim:

> The end point of the pipeline is a verdict, a diagnosis. That’s a small additional layer after we finish the object identification parts, I’ll get to it, but for now that can be mocked up by reporting pixel bundles for object identity for each object

He then explained why this is the natural diagnostic input, verbatim:

> Actually, the diagnosis part flows naturally from an output of pixel bundles for each object. After all, diagnoses are unnatural or damaged states of these objects, so if you have just the clean pixel bundles of every object, then that’s a super clean starting position from which to begin diagnosis

Implementation follows FULL_BUILD_PLAN §§16.6 and16.8. This record is the human instruction; current job state belongs only to the active task packet.
