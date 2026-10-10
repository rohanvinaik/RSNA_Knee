"""Template anatomy: bone masks, geometric landmarks, zone label volume.

Implements the research-fleet plan (docs/LANDMARK_PRIOR_ART.md, Ranks 1+3;
ADR decisions/2026-08-30-anatomical-zone-architecture.md): zones are derived
GEOMETRICALLY from template bone geometry — distance-transform joint gap,
condyle extremal points, notch saddle — then painted as a constant
template-space label volume every registered study indexes directly.

AXIS SEMANTICS (load-bearing; v5 canonical layout, chirality = RIGHT knee):
  axis 0: medial-lateral, 32 samples / 110mm — index 0 = LATERAL, 31 = MEDIAL
  axis 1: anterior-posterior, 224 / 150mm  — index 0 = ANTERIOR
  axis 2: inferior-superior, 224 / 150mm   — index 0 = INFERIOR

Sequence polarity note (fleet caveat): on fluid-sensitive fat-suppressed
MRI, fatty marrow is suppressed -> bone reads DARK; bone extraction is
low-intensity components INSIDE the knee mask. The one human artifact is a
single eye-QC of the template bone masks (render_qc output).
"""

from __future__ import annotations

import numpy as np
import scipy.ndimage as ndi

ZONE_NAMES = {
    0: "unzoned_background",
    1: "joint_line_slab",
    2: "retropatellar",
    3: "intercondylar_notch",
    4: "suprapatellar_recess",
    5: "popliteal",
    6: "medial_compartment",
    7: "lateral_compartment",
    8: "femur_bone",
    9: "tibia_bone",
    10: "patella_bone",
    11: "other_knee_tissue",
}


def classify_bone_groups(centroids: list, min_gap: float = 10.0) -> dict:
    """Group N dark-component centroids into patella/femur/tibia index lists.

    The knee FOV cuts the femoral shaft, so medial/lateral condyle marrow
    are DISCONNECTED islands (measured 2026-08-31) — "exactly 3 components"
    is the wrong premise. Pure decision over [(ml, ap, si), ...] (axis
    semantics above): patella = most ANTERIOR centroid (min ap); remaining
    components sorted by S-I and split at the LARGEST gap between adjacent
    centroids — the superior group is femur, the inferior tibia. A largest
    gap below `min_gap` voxels means the two bones don't separate cleanly:
    raise rather than fabricate. Requires >= 3 centroids.
    """
    if len(centroids) < 3:
        raise ValueError("need at least 3 bone centroids")
    patella = min(range(len(centroids)), key=lambda i: centroids[i][1])
    rest = sorted(
        (i for i in range(len(centroids)) if i != patella),
        key=lambda i: centroids[i][2],
    )
    gaps = [
        centroids[rest[j + 1]][2] - centroids[rest[j]][2] for j in range(len(rest) - 1)
    ]
    cut = max(range(len(gaps)), key=lambda j: gaps[j])
    if gaps[cut] < min_gap:
        raise ValueError(
            f"largest S-I gap {gaps[cut]:.1f} < {min_gap} — no clean split"
        )
    return {"patella": [patella], "tibia": rest[: cut + 1], "femur": rest[cut + 1 :]}


def bone_masks(
    template: np.ndarray,
    knee: np.ndarray,
    dark_pct: float = 30.0,
    min_size: int = 2000,
) -> dict:
    """Extract femur/tibia/patella masks from the template-study volume.

    Bone = dark (fat-sat marrow) large components inside the body mask:
    threshold at the `dark_pct` percentile of in-body intensity, in-plane
    open/fill, keep components >= min_size voxels, group into bones by
    centroid geometry (classify_bone_groups — femur/tibia may each be a
    UNION of islands because the FOV cuts the femoral shaft).
    """
    # The Otsu knee mask is a BRIGHT-tissue mask: dark marrow falls below its
    # threshold and connects to dark background through image edges in some
    # slices, so 3-D fill_holes never closes it — the mask EXCLUDES the bones
    # (measured 2026-08-31: 818k voxels <0.1 outside the mask vs 52k inside).
    # Per-slice 2-D fill along M-L builds a true body mask that encloses
    # marrow; erode it in-plane only (A-P/S-I ~0.67mm/voxel; M-L is 3.4mm and
    # 3-D erosion would eat it) so mask-rim artifacts can't win the
    # largest-dark-component contest.
    body = np.stack([ndi.binary_fill_holes(knee[i]) for i in range(knee.shape[0])])
    inplane = np.zeros((1, 3, 3), dtype=bool)
    inplane[0] = ndi.generate_binary_structure(2, 1)
    interior = ndi.binary_erosion(body, structure=inplane, iterations=8)
    thresh = np.percentile(template[body], dark_pct)
    dark = (template < thresh) & interior
    # opening stays in-plane too: default 3-D opening erodes 2 M-L voxels
    # (6.8mm/side) and severs the condyle-shaft marrow bridges
    dark = ndi.binary_opening(dark, structure=inplane, iterations=2)
    dark = ndi.binary_fill_holes(dark)
    lbl = np.zeros(dark.shape, dtype=np.int32)
    n = int(ndi.label(dark, output=lbl))
    sizes = ndi.sum(dark, lbl, range(1, n + 1))
    big = [i + 1 for i in range(n) if sizes[i] >= min_size]
    if len(big) < 3:
        raise RuntimeError(
            f"only {len(big)} bone candidates >= {min_size} voxels — "
            "check polarity/threshold"
        )
    comps = [lbl == k for k in big]
    cents = [tuple(np.argwhere(c).mean(axis=0)) for c in comps]
    groups = classify_bone_groups(cents)
    out = {}
    for name, idxs in groups.items():
        m = np.zeros(template.shape, dtype=bool)
        for j in idxs:
            m |= comps[j]
        out[name] = m
    return out


def femur_height_field(femur: np.ndarray) -> np.ndarray:
    """Distal femur surface: per (ml, ap) column, the min S-I index of femur
    (its most INFERIOR extent). Columns without femur = large sentinel."""
    ml, ap, si = femur.shape
    field = np.full((ml, ap), si + 10, dtype=np.int32)
    idx = np.argmax(femur, axis=2)  # first True along S-I (inferior-most)
    has = femur.any(axis=2)
    field[has] = idx[has]
    return field


def condyles_and_notch(femur: np.ndarray) -> dict:
    """Condyle distal points + notch saddle from the femur height field.

    Profile along M-L of the per-slice most-inferior femur extent: the two
    minima (most distal reaches) flanking a local maximum (the notch saddle)
    are the medial/lateral condyles. Deterministic argmin over the two
    halves split at the saddle.
    """
    field = femur_height_field(femur)
    valid = field < field.max()
    prof = np.where(valid.any(axis=1), np.min(field, axis=1), np.iinfo(np.int32).max)
    ok = np.nonzero(prof < np.iinfo(np.int32).max)[0]
    lo, hi = ok.min(), ok.max()
    mid = (lo + hi) // 2
    lat_c = lo + int(np.argmin(prof[lo:mid]))  # lateral condyle (low M-L)
    med_c = mid + int(np.argmin(prof[mid : hi + 1]))  # medial condyle (high M-L)
    notch_ml = lat_c + int(np.argmax(prof[lat_c : med_c + 1]))

    def point(ml_idx):
        ap_idx = int(np.argmin(field[ml_idx]))
        return (int(ml_idx), ap_idx, int(field[ml_idx, ap_idx]))

    return {
        "lateral_condyle": point(lat_c),
        "medial_condyle": point(med_c),
        "notch": point(notch_ml),
    }


def joint_line(femur: np.ndarray, tibia: np.ndarray) -> int:
    """Joint line S-I index: median midpoint between inferior femur edge and
    superior tibia edge over columns where both bones are present."""
    si = femur.shape[2]
    f_inf = np.where(femur.any(axis=2), np.argmax(femur, axis=2), -1)
    t_flip = tibia[:, :, ::-1]
    t_sup = np.where(tibia.any(axis=2), si - 1 - np.argmax(t_flip, axis=2), -1)
    both = (f_inf >= 0) & (t_sup >= 0) & (t_sup <= f_inf)
    if not both.any():
        raise RuntimeError("no femur-over-tibia columns — check bone masks")
    return int(np.median((f_inf[both] + t_sup[both]) / 2))


def build_zone_labels(template: np.ndarray, knee: np.ndarray, bones: dict) -> tuple:
    """Paint the zone label volume from template geometry. Returns
    (labels uint8 volume, landmarks dict)."""
    ml, ap, si = template.shape
    labels = np.zeros(template.shape, dtype=np.uint8)
    femur, tibia, patella = bones["femur"], bones["tibia"], bones["patella"]
    # Paint on the BODY mask (per-slice fill), not the Otsu bright mask: the
    # bright mask excludes marrow, which would leave the bone zones as
    # unzoned holes exactly where the bones are (same defect as bone_masks).
    body = np.stack([ndi.binary_fill_holes(knee[i]) for i in range(knee.shape[0])])
    jz = joint_line(femur, tibia)
    # Condyle distal points live AT the joint by definition (near-miss censor:
    # positions far below it are anatomically impossible). Restrict the height
    # field to a band around the joint line so in-plane femur/tibia marrow
    # merges (measured 2026-08-31) can't drag the argmin into the tibia.
    band = np.zeros_like(femur)
    band[:, :, max(0, jz - 8) :] = True
    lm = condyles_and_notch(femur & band)
    lm["joint_line_si"] = jz

    pat_idx = np.argwhere(patella)
    pat_ap_max = int(pat_idx[:, 1].max())  # posterior patella surface
    pat_si_top = int(pat_idx[:, 2].max())  # superior patella pole
    fem_ap = np.argwhere(femur)
    fem_ap_min = int(np.percentile(fem_ap[:, 1], 5))  # anterior femur surface
    fem_ap_max = int(np.percentile(fem_ap[:, 1], 95))  # posterior femur surface
    notch_ml_idx = lm["notch"][0]

    mlg, apg, sig = np.mgrid[0:ml, 0:ap, 0:si]

    slab = np.abs(sig - jz) <= 15  # ~10mm joint-line slab
    lat_half = mlg < notch_ml_idx
    med_half = mlg > notch_ml_idx
    notch_box = (
        (np.abs(mlg - notch_ml_idx) <= 3)
        & (np.abs(sig - jz) <= 25)
        & (apg >= fem_ap_min)
        & (apg <= fem_ap_max)
    )
    retro = (
        (apg > pat_ap_max)
        & (apg <= pat_ap_max + 15)
        & (sig >= jz - 10)
        & (sig <= pat_si_top + 10)
    )
    supra = (sig > pat_si_top) & (apg < fem_ap_min + 10)
    popl = (apg > fem_ap_max) & (np.abs(sig - jz) <= 40)

    # paint order = precedence (later never overwrites earlier)
    for zid, mask in (
        (8, femur),
        (9, tibia),
        (10, patella),
        (3, notch_box),
        (2, retro),
        (4, supra),
        (5, popl),
        (6, slab & med_half),
        (7, slab & lat_half),
    ):
        labels[(labels == 0) & body & mask] = zid
    labels[(labels == 0) & body] = 11
    return labels, lm
