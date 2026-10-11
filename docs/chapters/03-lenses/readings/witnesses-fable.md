# Consult reply: `knee.lenses.witnesses`

I accept the frame as stated. Where I say "known" below I mean standard knee-MRI anatomy and physics I am confident of; "inferred" means a consequence I am drawing for your pipeline; "uncertain" means I would check before relying on it.

---

## 1. Attacking the admission criteria

### Subcutaneous — "between the skin envelope and the first dark line inward, seeded against air"

**Known cases that pass structure but are not fat:**

- **Dermis.** The compartment starts at the air boundary, and the first 1–3 mm inward is skin, which is intermediate on T1 and PD and *not* dark on FS. If the dermis is thin enough to be the "first dark line", the compartment is zero-thickness; if it isn't, it is inside the compartment. Either way the population includes a non-fat band exactly at its most reliable edge.
- **The great saphenous vein and tributaries**, medially, run *inside* subcutaneous fat at knee level, 3–5 mm across — bright on fluid-sensitive sequences with flow artifact, and large enough to pass a physical-support test. The saphenous nerve accompanies it.
- **Subcutaneous edema** (post-traumatic, post-surgical, dependent/venous, cellulitis) is reticular bright signal on FS threaded through the fat. This is common in exactly the knees in your corpus. The population becomes a mixture that the structural criteria cannot see.
- **Prepatellar / pretibial bursitis**: fluid *in* the subcutaneous compartment anteriorly, against air, bounded inward by the patellar tendon's dark band — satisfies every structural clause.
- **Chemical-shift misregistration** (known physics): every fat/water interface carries a one-to-two-pixel bright/dark band in the frequency-encode direction. The skin–fat and fat–fascia boundaries are both corrupted on the same side. This is not partial volume and is not removed by "support fits inside".
- **Spectral fat-saturation failure** is worst at the air–skin interface and off-isocenter (B0 inhomogeneity, susceptibility at the surface). Known and common over the anterior patella and at the periphery of a large knee. So on FS series the subcutaneous witness is the *most* likely of the three to be bright when it should be dark — and it is the one you would naively trust most.

**Inferred:** the subcutaneous witness is structurally the easiest to find and acquisitionally the least reliable. Your three-step admission is right; step two (acquisition evidence) must be where most subcutaneous refusals happen, and the stage must report that as its own code.

### Marrow — "interior of a B1 dome bounded by dark cortex"

- **Red (hematopoietic) marrow.** Known: metaphyseal red marrow in the distal femur and proximal tibia is common in adults under ~40, women, smokers, obese patients, athletes. It is intermediate on T1 and mildly bright on FS. If the dome continues past the physeal scar into the metaphysis, the interior is a two-population mixture. Epiphyses are fatty from early childhood, so a dome bounded by the physeal scar is the safe object; a dome that includes the metaphysis is not.
- **Trabecular bone.** Known: marrow is fat plus trabeculae plus hematopoietic cells. Subchondral trabecular density is high, so the dome interior near the plate is intermediate, not fat-bright. On any gradient-echo series marrow is markedly darker than subcutaneous fat for T2*/susceptibility reasons alone.
- **Bone marrow lesions** (contusion, subchondral edema, stress reaction) are a finding on the label list. An interference screw after ACL reconstruction sits *inside* the tibial and femoral tunnels, i.e. inside your marrow domes, with susceptibility bloom and local FS failure. Enchondroma (common distal femur), bone infarct, subchondral cyst, intraosseous ganglion are all bright-on-FS interior content.

**The attack that matters most (inferred, high confidence):** marrow fat and subcutaneous fat are *not the same tissue at a different radius*. Even with a perfectly flat coil, marrow reads lower on T1/PD than subcutaneous fat (trabecular partial volume, lower proton density) by an amount that depends on sequence type and is not known to you. Therefore **between-witness disagreement = coil bias + tissue offset**, and the two are confounded. The three-legged stool is valid only if the legs are measuring the same quantity. They are not. I address what to do about this in §5 and §7.

### Hoffa's — "interstice between patellar tendon's dark band and the femoral trochlea"

- **The posterior boundary is wrong in most of the sagittal stack.** Known: the trochlea bounds Hoffa's only superiorly. In the midline the posterior neighbour is the intercondylar notch, the ACL and the anterior recess of the joint; medially and laterally it is the anterior horns of the menisci, the transverse meniscal ligament and the tibial plateau. A tendon-to-trochlea interstice as stated will contain joint fluid, meniscal anterior horn and ligament.
- **Normal internal structure:** the infrapatellar plica (ligamentum mucosum), vessels bright on FS, horizontal and vertical synovial clefts holding fluid, the deep infrapatellar bursa between tendon and tibia (a few mm of fluid is normal).
- **Pathology that is in the corpus by selection:** superolateral Hoffa's edema (impingement), post-arthroscopic portal fibrosis (the anteromedial and anterolateral portals pass *through* Hoffa's), cyclops lesion after ACL reconstruction at its posterior margin, and any effusion, which displaces and infiltrates the pad.

**Inferred:** Hoffa's will be the witness refused most often by a correct homogeneity test, and absent outright after surgery. Design for its absence as the common case, not the exception.

### Muscle — "large compartment touching neither air nor bone interior, bounded by fascia"

**Known:** at joint level the knee is mostly tendon. The muscle present is distal vastus medialis/lateralis above, gastrocnemius heads and popliteus and plantaris behind, each striated with fatty septa on T1. Meanwhile the following objects satisfy "large, fascia-bounded, touching neither air nor bone interior":

- a **Baker's cyst** (popliteal cyst) — very common in abnormal knees, posteromedial, wall-bounded;
- a **distended suprapatellar pouch** (effusion), capsule-bounded;
- **Hoffa's fat pad** itself;
- the **popliteal neurovascular bundle** with its fat — and the popliteal artery throws **phase-encode ghosts** across the whole image; on sagittal series phase-encode is usually anterior–posterior, so those ghosts cross Hoffa's and the anterior subcutaneous fat.

**Inferred:** "large and fascia-bounded" is a description of a compartment, not an identity of muscle. Muscle needs a structural clause that only muscle satisfies: it attaches to bone (gastrocnemius heads to the posterior condyles, VMO to the patella), it is elongated along the limb axis, and it has internal pennate striation. Fatty atrophy in older patients then shows up honestly as a mixture refusal rather than being admitted as a wider band.

---

## 2. The circularity

You have not escaped it as written, but there is a genuinely non-circular floor, and it is one you already built.

**Known physics:** in air, magnitude MR data is Rayleigh-distributed with a fixed mean/sd ratio (~1.91). The air region is identified by connectivity to the frame plus Rayleigh identity — no tissue witness is involved. After your variance-stabilising transform, "dark" has an absolute meaning: *indistinguishable from the noise floor within k flickers*. Cortex, tendon, ligament and meniscus — your "dark on everything" class — are floor-dark on TSE, not merely darker than something else.

**Non-circular order (inferred):**

0. Noise floor from Rayleigh air.
1. Floor-dark objects by geometry alone (closed curves, bands).
2. Interiors bounded by closed floor-dark curves → B1 domes → **marrow is the first witness, admitted without any fat-relative reading.**
3. Only now does "bright relative to a witness" exist. Subcutaneous fat's inner boundary (fascia) is *not* floor-dark — it is a thin partial-volumed line visible only *relative to fat* — so the subcutaneous compartment is found as "the place against air whose population matches marrow's digit class", i.e. admitted *against* marrow. Hoffa's and muscle follow.

**The smallest honest circularity to declare:** witness #1 (marrow) is admitted on floor-darkness and geometry only; witnesses #2–#4 are admitted by reading against #1 and then serve as checks on #1. This is not vicious because the first step uses a standard that is not a tissue (the noise floor) and because the later witnesses can *refuse* #1 — if subcutaneous and Hoffa's agree and marrow disagrees with both by more than the band, marrow's admission is revoked and the stage says so.

**Uncertain:** on 3D gradient-echo series (DESS, MEDIC, FLASH), which some knee protocols include, cortex is floor-dark but marrow is also near-dark and fat is intermediate. The whole table is TSE-specific. Step 0 should refuse the series type, not try to find witnesses in it.

**Known caveat on step 0:** with parallel imaging the noise is spatially non-stationary (g-factor) and highest centrally; the Rayleigh air estimate is a lower bound on the central sigma. And if a vendor intensity correction was applied before export, the air is no longer Rayleigh and the central noise is amplified. See §6.

---

## 3. Homogeneity without a tuned threshold

Two things first. (a) Marrow has intrinsic texture (trabeculae), so "spread equals one flicker" would refuse every marrow witness; the test cannot be *spread versus noise*. (b) Any one-sided rule "refuse if X > c" is a cut unless c is already an argument the stage carries.

**Proposal (inferred): test the witness against itself with `digit_code`, using splits that are structural and named, and the same `k` the stage already carries.**

Split the candidate population along axes that come from structure, not intensity: anterior/posterior, superior/inferior, inner/outer (near-boundary vs deep), and by connected component. For each split, state one half against the other using `digit_code` with the band computed from the **noise sigma and the medians' estimation precision only** (median standard error ≈ 1.25·σ/√n per half, in flickers — this is the "precision" failure you want kept separate), *not* from the pooled spread. If every named split returns `0`, the population is admitted. If any split returns `±`, the population is a mixture *along that axis*, and the axis is reported:

- inner/outer ± in subcutaneous → chemical shift, dermis, or FS failure at the surface;
- superior/inferior ± in marrow → red marrow past the physeal scar;
- anterior/posterior ± in Hoffa's → fluid in the anterior recess or portal scar;
- component vs component ± anywhere → two objects were merged.

This is deterministic, introduces no new constant, and the refusal names the step and the axis. The one thing it does not catch is a *fine-grained* mixture (edema reticulated through fat at sub-split scale). For that, emit — do not threshold — the ratio of the population's robust spread (MAD-scaled) to the noise sigma, in flickers, as a witness property. A subcutaneous witness reading 1.2 flickers and a marrow witness reading 2.5 are both admitted; the digit band carries the difference honestly because it is real texture, not a hidden mixture. A witness whose halves agree but whose spread is large is textured; a witness whose halves disagree is a mixture. Those are the two failures you asked to keep apart, and this separates them.

**Uncertain:** whether residual spatial correlation (neighbour correlation beyond what zero-filled interpolation produces) could serve as a parameter-free mixture detector. I think the vendor interpolation confound makes it unreliable across scanners; I would not build on it.

---

## 4. Refusing a fluid witness

**Refuse it. You are right, with one amendment.**

**Known:** normal knees hold a trace of physiological fluid (posterior condylar recesses, deep infrapatellar bursa), never enough to satisfy physical support. Popliteal vein blood is bright on T2 TSE but flow-dependent. Nothing reliably present in every knee gives a fluid standard. A distended recess is the effusion finding; its presence as a witness would be label-coupled, and silence on fluid-dependent rows would then correlate with the label — which your laws forbid letting anyone read as a negative, but which you should not build in regardless.

**The amendment:** your table's cartilage row is *"below fluid, above meniscus"*, and the cartilage-defect finding is precisely "fluid where cartilage should be". Without a fluid witness, on PD-FS the fluid/cartilage distinction is one of degree — both are above fat, both well above the floor. Two things rescue it without a fluid witness:

- **T1 (and non-FS PD):** fluid is *below muscle*, cartilage is *at or above muscle*. That row already exists in your design and is the honest separator when a T1 or non-FS series exists.
- **The physical ceiling:** on fluid-sensitive TSE, free fluid has the longest T2 in the knee; nothing normal is brighter except flowing blood, the physis in adolescents, and artifact. "Fluid" can be stated as *at the ceiling of the admitted-tissue range*, which is a relation to physics, not a manufactured witness.

**Uncertain:** whether every study in the corpus has a T1 or non-FS series. If some have only FS series, the cartilage/fluid row is weaker there and the stage should say so by series inventory, not by inventing a fluid level.

---

## 5. Three rows or one

The stool principle applies to witnesses disagreeing *about the same thing*. A place in the lateral subcutaneous fat stated against Hoffa's is not a second opinion about that place's tissue; it is a reading of the coil profile between two positions, confounded (§1) with a tissue offset. Three rows per place would be three partially-different questions presented as one, and the conjunction would silently fail wherever Hoffa's is absent, which is often.

**Recommendation (inferred):**

- **One tissue row**, stated against the *nearest admitted* fat witness by in-slice distance (a proxy for coil distance — the coil geometry is not in your hands), with provenance recording which witness and whether the slice or series middle was used.
- **One stability digit per place:** `0` if the tissue digit is the same against every admitted fat witness, `±` if it flips, silent if only one is admitted. This is the stool principle in one digit: it marks exactly the places where the bias field (or the tissue offset) changes the answer, without tripling every row.
- **The bias reading is a separate stage output, not a per-place row.** And because of §1's confound, the clean bias measurement is *within*-witness, not between: the subcutaneous ring at different azimuths is the same tissue at different coil distances; the medial condyle, lateral condyle, tibial epiphysis and patella are the same tissue (marrow) at different positions and the tissue offset cancels in their differences. Between-witness differences (marrow vs subcutaneous) carry an unknown offset and should be emitted as such — labelled as confounded — not as "the bias field".

---

## 6. What breaks first at scale

Ranked by my estimate of how early across 58 mixed studies:

1. **Fat-suppression heterogeneity** (known: spectral fat-sat, STIR, Dixon water, water-excitation all exist in knee protocols and are not interchangeable). Spectral FS fails at the periphery and over the patella — the subcutaneous witness location — on a large fraction of series. On STIR, everything short-T1 is dark, not only fat. On Dixon, fat/water swaps invert an entire connected region: subcutaneous fat comes back *bright* on the "water" image with perfect internal homogeneity, so the split test in §3 passes. **Output signature:** the fat witnesses' disagreement pattern on the FS series does not match their pattern on the non-FS series of the same study. Coil sensitivity is series-independent within a study (same coil, same position — mostly), so this mismatch is a self-check you can run; a study where FS-series disagreement ≫ non-FS disagreement has an FS problem, not a coil problem. The FS mechanism must be an argument to the stage.
2. **Vendor pre-normalisation** (known to exist: Siemens prescan-normalise, GE PURE/SCIC, Philips CLEAR). In those studies the bias field is already flattened, the air is no longer Rayleigh, and the central noise is amplified. **Signature:** witnesses agree suspiciously well, step-0 sigma is underestimated, and spurious `±` digits cluster in the centre of the knee (notch, cruciates, posterior horns) for one scanner's studies only.
3. **Hoffa's absent or refused** in post-arthroscopic knees and effusions. Signature: the stability digit is silent across the anterior compartment in those studies; harmless if the one-row design is used, catastrophic if the three-row conjunction is.
4. **Red marrow and hardware inside domes**: signature is marrow refused on the superior/inferior split in younger patients and on the component split in reconstructed knees.
5. **GRE series** present in some protocols breaking the table outright (§2).

I am confident of 1 and 5 as physics; 2 is a real mechanism but I am uncertain how many studies carry it; 3 and 4 are population-dependent.

---

## 7. What you are not asking

- **Chemical-shift direction.** It is in the header (frequency-encode axis) and corrupts every witness boundary by one to two pixels on one side only. Eligibility erosion must be *anisotropic in-plane*, and the direction must be an argument.
- **Through-plane support.** Your "native measurement support" must be anisotropic: slice thickness (3–4 mm) is typically ten times the pixel. A fat sliver that is wide in-plane but one slab thick is partial volume through-plane; `slab_code` governs gaps, but eligibility must also respect slab thickness.
- **Witness/target entanglement for marrow.** Bone marrow lesion is a label. The rule for which bone witnesses which must be stated before any evaluation and must not be chosen by looking at labels — e.g. a condyle's marrow row is read against the *other* bones' marrow, and when all domes are refused the row is silent. Bilateral lesions will then be silent, correctly.
- **Series inventory as a first-class input.** The table assumes non-FS, FS, T2 and T1 all exist. Rows that need an absent series must be silent by inventory, and the inventory should be emitted so silence is attributable.
- **Phase-encode ghosting** from the popliteal artery across Hoffa's and anterior subcutaneous fat: its direction is also in the header and is the one artifact that places bright structure *inside* an otherwise valid witness in a straight line.
- **Median precision as a declared quantity.** You already separate precision from heterogeneity; make precision (≈1.25σ/√n, in flickers) a witness property that legitimately enters the band, so that a per-slice fallback to series is a change in precision, not a change in population.
- **The marrow–subcutaneous tissue offset** (§1, §5) is the thing most likely to be misread as bias field and then "corrected". Decide now that between-witness disagreement is emitted as *confounded* and that only within-witness, same-tissue differences are called bias.

Where I am least sure: the exact corpus composition (series types, FS methods, pediatric fraction, surgical fraction, vendor normalisation). Everything above that depends on those is conditional, and the stage should discover them from the series rather than assume.