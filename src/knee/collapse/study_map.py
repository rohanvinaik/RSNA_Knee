"""One study's three-plane map: key planes -> positions -> all-pairs vectors -> expected slice AND in-plane place.

(`docs/RELATIVE_POSITION_MAP.md` §0 and §8.8.) The study-level bookkeeping over `knee.collapse.relative`'s geometry.
Pure: no pixels, no statistics, no anatomy numbers of its own, no centroids. The anatomical ideal is an INJECTED
callable (`ideal(origin, target, knee_scale_mm) -> relative.IdealVector | None`, the parent's `knee.collapse.anatomy_map`); the
study map never invents one, so without it nothing is predicted and nothing else is lost.

**One anatomy, many series.** A study's fat-bright and fat-dark series of one orientation are different images of
ONE knee. Each family that selects a native plane for an object offers it as a candidate (`StudyMap.offer`) with the
measured support it was selected on, the source series and slice and the reason. Per object and orientation ONE key
plane is selected from the candidates: candidates on the same physical plane are one plane (the best supported of
them speaks for it); of physically distinct planes the one with the greatest support; an exact tie of distinct planes
is `tied` (nothing is picked); a candidate with no measured support is evidence only, and with no supported one and
several distinct planes the object is `tied` too. Coordinates are never averaged and every candidate is kept.

**Position and vectors.** `relative.reference_position` per object, for every name in `OBJECTS` (`OBJECT_CODES` but `unassigned`, and `recess`)
(complete, or partial with its constraints); `pair_table` holds every ORDERED pair: a complete vector, or a named
row saying which end has no complete position and why.

**Predictions and guides.** For each target and each complete observed anchor with an ideal vector,
`relative.expected_point`: one distinct prediction per anchor, never merged; the spread between them and the residual
to the target's own observed position are kept. `guide` translates them into one series' own frames
(`relative.locate_in_image`): each prediction's nearest slice and in-plane (row, column); the slice window runs from
the nearest slice of the lowest to that of the highest prediction, so disagreement widens the look and is not averaged.
The consumer looks there first and falls back to its full search when the look fails; `note_use` counts which.

**The scale and the cache.** One explicit knee scale (`set_scale`, the femur's observed mediolateral breadth, or
unknown) is held once and passed with every ideal query (`ideal(origin, target, knee_scale_mm)`, the anatomy
module's own signature) and to the pair vectors; an unknown scale is the reference's own millimetres and is never
claimed as measured. Positions, per-target predictions and guides are solved once per map VERSION: new plane
evidence or a changed scale bumps the version and drops them, so dozens of identical guide calls cost one solve.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from knee.objects.assignments import OBJECT_CODES

# the actual object codes but unassigned, and the semantic name `recess` the receipts also carry (the anatomical
# reference's MAP_OBJECTS: 43 names; no code is invented for the others)
OBJECTS = (*(name for name in OBJECT_CODES if name != "unassigned"), "recess")
Ideal = Callable[[str, str, "float | None"], "rel.IdealVector | None"]
SAME_PLANE_MM = 1e-6


@dataclass(frozen=True)
class Candidate:
    """One series' selected (or unselectable) native plane for an object in one orientation."""

    plane: rel.KeyPlane
    support: float | None
    source: str


@dataclass(frozen=True)
class Prediction:
    """Where the ideal says `object` lies given one observed anchor: an expectation, never a position."""

    object: str
    anchor: str
    status: str
    point_lps: rel.Triple | None
    ideal_source: str


@dataclass(frozen=True)
class Guide:
    """Where to look first for `object` in one series: `status` is `guided` or `unguided:<reason>`; `slices` the
    inclusive window from the lowest to the highest prediction's nearest slice; `rcs` each prediction's in-plane
    (row, column) on its own nearest slice; `placements` every prediction's full placement; `spread_mm` the largest
    distance between two predictions (None for fewer than two)."""

    object: str
    series_uid: str
    status: str
    slices: tuple[int, ...] = ()
    rcs: tuple[tuple[int, tuple[float, float]], ...] = ()
    placements: tuple[dict, ...] = ()
    spread_mm: float | None = None
    anchors: tuple[str, ...] = ()
    half_px: tuple[float, float] | None = None


def _same_plane(a: rel.KeyPlane, b: rel.KeyPlane) -> bool:
    if a.normal is None or b.normal is None:
        return False
    na, nb = np.asarray(a.normal), np.asarray(b.normal)
    dot = float(na @ nb)
    flip = 1.0 if dot > 0 else -1.0
    return (
        abs(abs(dot) - 1.0) <= 1e-9
        and abs(a.offset_mm - flip * b.offset_mm) <= SAME_PLANE_MM
    )


@dataclass
class StudyMap:
    knee: str | None = None
    scale: rel.KneeScale = rel.UNKNOWN_SCALE
    names: tuple[str, ...] = OBJECTS
    candidates: dict[tuple[str, str], list[Candidate]] = field(default_factory=dict)
    refinements: list[dict] = field(default_factory=list)
    uses: Counter = field(default_factory=Counter)
    use_rows: list[dict] = field(default_factory=list)
    version: int = 0
    _solved: dict = field(default_factory=dict, repr=False)

    # ---- the version, the scale and what is solved for it
    def _bump(self) -> None:
        self.version += 1
        self._solved = {}

    def set_scale(self, scale: rel.KneeScale) -> None:
        """The knee's explicit scale; a different one is new evidence (the vectors and the ideal change)."""
        if scale != self.scale:
            self.scale = scale
            self._bump()

    # ---- evidence in
    def offer(
        self,
        object: str,
        plane: rel.KeyPlane,
        support: float | None = None,
        source: str = "",
    ) -> None:
        """A series' selected plane (or its named non-selection) for `object`. Unknown objects are refused."""
        if object not in self.names:
            raise ValueError(f"not an anatomical object of the map: {object}")
        if plane.object != object:
            raise ValueError("the plane belongs to another object")
        clean = (
            None
            if support is None or not math.isfinite(float(support))
            else float(support)
        )
        held = self.candidates.setdefault((object, plane.orientation), [])
        new = Candidate(plane, clean, source)
        if new in held:
            return  # the same family offering the same plane again adds no evidence
        held.append(new)
        self._bump()

    def refine(
        self, object: str, planes: Sequence[tuple[rel.KeyPlane, float | None, str]]
    ) -> None:
        """A later family's complete or partial object enters the map; its offers are logged as a refinement."""
        for plane, support, source in planes:
            self.offer(object, plane, support, source)
        self.refinements.append(
            {
                "object": object,
                "orientations": sorted({p.orientation for p, _, _ in planes}),
                "sources": sorted({s for _, _, s in planes}),
                "version": self.version,
            }
        )

    # ---- one key plane per object and orientation
    def selected(self, object: str, orientation: str) -> rel.KeyPlane:
        found = self.candidates.get((object, orientation), [])
        usable = [c for c in found if c.plane.usable]
        if not usable:
            if found:
                first = found[0].plane
                return rel.unresolved_plane(
                    object,
                    orientation,
                    first.outcome
                    if first.outcome in rel.UNRESOLVED_OUTCOMES
                    else rel.REFUSED,
                    reason=first.reason or first.outcome,
                    provenance=first.provenance,
                )
            return rel.unresolved_plane(
                object,
                orientation,
                rel.NOT_SUPPLIED,
                reason="no family offered a plane",
            )
        groups: list[list[Candidate]] = []
        for c in usable:
            for g in groups:
                if _same_plane(g[0].plane, c.plane):
                    g.append(c)
                    break
            else:
                groups.append([c])

        def best(g: list[Candidate]) -> Candidate:
            return max(g, key=lambda c: -1.0 if c.support is None else c.support)

        heads = [best(g) for g in groups]
        supported = [h for h in heads if h.support is not None]
        if len(groups) > 1:
            top = max(
                (h.support for h in supported if h.support is not None), default=None
            )
            winners = (
                [h for h in supported if h.support == top] if top is not None else heads
            )
            if len(winners) != 1:
                return rel.unresolved_plane(
                    object,
                    orientation,
                    rel.TIED,
                    reason="distinct planes with equal or unmeasured support; none is picked",
                    candidates=[(h.plane.series_uid, h.plane.slice) for h in winners],
                )
            head = winners[0]
        else:
            head = heads[0]
        p = head.plane
        note = f"selected among {len(usable)} offered plane(s) by greatest measured support ({head.support}); source {head.source}"
        return rel.KeyPlane(
            p.object,
            p.orientation,
            p.outcome,
            p.series_uid,
            p.slice,
            p.normal,
            p.offset_mm,
            p.precision_mm,
            f"{p.reason}; {note}" if p.reason else note,
            p.provenance,
            p.candidates,
        )

    # ---- positions and pairs
    def positions(self) -> dict[str, rel.Position]:
        """Every object's position, solved once per version."""
        if "positions" not in self._solved:
            self._solved["positions"] = {
                name: rel.reference_position(
                    name, [self.selected(name, o) for o in rel.ORIENTATIONS]
                )
                for name in self.names
            }
        return dict(self._solved["positions"])

    def pair_table(
        self, positions: Mapping[str, rel.Position] | None = None
    ) -> tuple[dict[tuple[str, str], rel.PairVector], list[dict]]:
        """Every ordered pair of the map's objects: the complete vectors and a named row for each other pair."""
        held = positions if positions is not None else self.positions()
        if "vectors" not in self._solved:
            self._solved["vectors"] = rel.pair_vectors(held, self.scale, self.knee)[0]
        vectors = self._solved["vectors"]
        rows = []
        for a in self.names:
            for b in self.names:
                if a == b or (a, b) in vectors:
                    continue
                missing = [n for n in (a, b) if not held[n].complete]
                rows.append(
                    {
                        "origin": a,
                        "target": b,
                        "unresolved_endpoints": missing,
                        "statuses": {n: held[n].status for n in missing},
                    }
                )
        return vectors, rows

    # ---- predictions
    def predictions_for(self, target: str, ideal: Ideal | None) -> list[Prediction]:
        """One target's expectations, one per complete anchor with an ideal: solved once per version and ideal."""
        key = ("predictions", id(ideal), target)
        if key not in self._solved:
            held = self.positions()
            found: list[Prediction] = []
            for anchor in self.names:
                if anchor == target or not held[anchor].complete or ideal is None:
                    continue
                vector = ideal(anchor, target, self.scale.mm)
                if vector is None:
                    continue
                got = rel.expected_point(held[anchor], vector, self.knee)
                found.append(
                    Prediction(
                        target, anchor, got.status, got.point_lps, got.ideal_source
                    )
                )
            self._solved[key] = found
        return list(self._solved[key])

    def predictions(self, ideal: Ideal | None) -> dict[str, list[Prediction]]:
        return {n: self.predictions_for(n, ideal) for n in self.names}

    # ---- translation into one series
    def guide(
        self,
        object: str,
        series_uid: str,
        frames: Sequence[PlaneFrame | None],
        shape_rc: tuple[int, int] | None,
        ideal: Ideal | None,
        half_span_lps: Sequence[float] | None = None,
    ) -> Guide:
        """`half_span_lps` is the anatomical allowance (half the object's reference extent along each patient axis,
        the anatomy module's `target_span_mm`): the window also takes every slice within that reach of a
        prediction along the slice's own normal, and the in-plane box is that reach in this image's pixels.
        None = the predictions' own range only. Solved once per version, ideal, series and allowance."""
        key = (
            "guide",
            id(ideal),
            object,
            series_uid,
            None if half_span_lps is None else tuple(float(v) for v in half_span_lps),
            None if shape_rc is None else tuple(shape_rc),
            len(frames),
        )
        if key not in self._solved:
            self._solved[key] = self._guide(
                object, series_uid, frames, shape_rc, ideal, half_span_lps
            )
        return self._solved[key]

    def _guide(
        self,
        object: str,
        series_uid: str,
        frames: Sequence[PlaneFrame | None],
        shape_rc: tuple[int, int] | None,
        ideal: Ideal | None,
        half_span_lps: Sequence[float] | None,
    ) -> Guide:
        if ideal is None:
            return Guide(object, series_uid, "unguided:no_anatomical_ideal_supplied")
        preds = self.predictions_for(object, ideal)
        used = [p for p in preds if p.status == "expected" and p.point_lps is not None]
        if not used:
            reason = (
                "no_complete_anchor_with_an_ideal"
                if not preds
                else "predictions_not_expected"
            )
            return Guide(object, series_uid, f"unguided:{reason}")
        places = [rel.locate_in_image(p.point_lps, frames, shape_rc) for p in used]
        rows = tuple(
            {
                "anchor": p.anchor,
                "point_lps": list(p.point_lps) if p.point_lps else None,
                "status": q.status,
                "slice": q.slice,
                "rc": None if q.rc is None else list(q.rc),
                "off_plane_mm": q.off_plane_mm,
                "tied_slices": list(q.tied_slices),
            }
            for p, q in zip(used, places, strict=True)
        )
        slices = [q.slice for q in places if q.slice is not None]
        if not slices:
            return Guide(
                object, series_uid, "unguided:" + places[0].status, placements=rows
            )
        pts = np.array([p.point_lps for p in used], dtype=float)
        half_px = None
        window = set(range(min(slices), max(slices) + 1))
        if half_span_lps is not None:
            half = np.abs(np.asarray(half_span_lps, dtype=float))
            held = [(i, f) for i, f in enumerate(frames) if f is not None]
            for i, f in held:
                n = np.asarray(f.normal(), dtype=float)
                reach = float(np.abs(n) @ half)
                if any(abs(float(n @ (pt - f.origin_lps))) <= reach for pt in pts):
                    window.add(i)
            f0 = held[0][1]
            inverse = np.abs(np.linalg.pinv(np.asarray(f0.basis_lps, dtype=float)))
            half_px = (float(inverse[0] @ half), float(inverse[1] @ half))
        spread = None
        if len(pts) > 1:
            spread = float(max(np.linalg.norm(a - b) for a in pts for b in pts))
        rcs = tuple(
            (q.slice, (q.rc[0], q.rc[1]))
            for q in places
            if q.slice is not None and q.rc is not None
        )
        return Guide(
            object,
            series_uid,
            "guided",
            tuple(sorted(window)),
            rcs,
            rows,
            spread,
            tuple(p.anchor for p in used),
            half_px,
        )

    def note_use(self, object: str, series_uid: str, outcome: str, **detail) -> None:
        """A consumer's account of a guide: guided_hit, guided_miss_then_full_search, unguided_full_search ..."""
        self.uses[outcome] += 1
        self.use_rows.append(
            {"object": object, "series_uid": series_uid, "outcome": outcome, **detail}
        )

    # ---- the receipt
    def record(self, ideal: Ideal | None = None) -> dict:
        """The whole map as plain data, serialized ONCE (the file of the study; the series' records keep only
        `summary`). Every source (the series and the family that offered a plane) is in the `sources` table and
        evidence rows name it by `source_id`; every complete pair is one row addressed by its two object
        names with its distance, its displacement and unit direction in the patient frame (LPS) and in the
        anatomical frame (medial, posterior, superior) and its displacement against the knee scale; a pair
        with an unresolved end keeps an explicit ordered-pair row naming its unresolved endpoints and
        their statuses. Detailed plane evidence stays in the object table rather than being copied per pair."""
        positions = self.positions()
        vectors, unresolved = self.pair_table(positions)
        preds = self.predictions(ideal)
        sources: dict[tuple[str, str], int] = {}

        def source_id(series_uid: str, source: str) -> int:
            return sources.setdefault((series_uid, source), len(sources))

        rows = {}
        for name, pos in positions.items():
            mine = preds[name]
            expected = [p for p in mine if p.status == "expected" and p.point_lps]
            disagreement = None
            if len(expected) > 1:
                pts = np.array([p.point_lps for p in expected], dtype=float)
                disagreement = float(
                    max(np.linalg.norm(a - b) for a in pts for b in pts)
                )
            residuals = {}
            if pos.complete and pos.point_lps is not None:
                for p in expected:
                    residuals[p.anchor] = float(
                        np.linalg.norm(
                            np.asarray(p.point_lps) - np.asarray(pos.point_lps)
                        )
                    )
            rows[name] = {
                "status": pos.status,
                "geometry": pos.geometry,
                "point_lps": None if pos.point_lps is None else list(pos.point_lps),
                "precision_mm": None
                if pos.precision_mm is None
                else list(pos.precision_mm),
                "problems": dict(pos.problems),
                "line_direction": None
                if pos.line_direction is None
                else list(pos.line_direction),
                "key_planes": {
                    o: self.selected(name, o).address() for o in rel.ORIENTATIONS
                },
                "evidence": {
                    o: [
                        {
                            "slice": c.plane.slice,
                            "outcome": c.plane.outcome,
                            "normal": None
                            if c.plane.normal is None
                            else list(c.plane.normal),
                            "offset_mm": None
                            if math.isnan(c.plane.offset_mm)
                            else c.plane.offset_mm,
                            "support": c.support,
                            "source_id": source_id(c.plane.series_uid, c.source),
                        }
                        for c in self.candidates.get((name, o), [])
                    ]
                    for o in rel.ORIENTATIONS
                },
                "predictions": [
                    {
                        "anchor": p.anchor,
                        "status": p.status,
                        "point_lps": None if p.point_lps is None else list(p.point_lps),
                    }
                    for p in mine
                ],
                "prediction_disagreement_mm": disagreement,
                "residual_to_observed_mm": residuals,
            }
        complete = sorted(n for n, p in positions.items() if p.complete)
        ideal_sources = sorted(
            {p.ideal_source for plist in preds.values() for p in plist}
        )
        return {
            "schema": "study_map/v1",
            "construction": "three_key_planes",
            "knee": self.knee,
            "scale": {
                "mm": self.scale.mm,
                "source": self.scale.source,
                "code": self.scale.code,
                "unit": "millimetres of the femur's mediolateral breadth, or unknown: then the "
                "reference's own millimetres are used and never claimed as measured",
            },
            "ideal": "supplied"
            if ideal is not None
            else "no_anatomical_ideal_supplied",
            "ideal_sources": ideal_sources,
            "version": self.version,
            "sources": [
                {"id": i, "series_uid": uid, "source": text}
                for (uid, text), i in sources.items()
            ],
            "objects": rows,
            "counts": {
                "objects": len(self.names),
                "complete": len(complete),
                "partial": sum(
                    1 for p in positions.values() if p.status == rel.PARTIAL
                ),
                "ordered_pairs": len(self.names) * (len(self.names) - 1),
                "pairs_complete": len(vectors),
                "pairs_unresolved": len(unresolved),
                "predictions": sum(len(v) for v in preds.values()),
                "refinements": len(self.refinements),
                "uses": dict(self.uses),
            },
            "pairs_complete": [
                {
                    "origin": a,
                    "target": b,
                    "displacement_lps": list(v.displacement_lps),
                    "magnitude_mm": v.magnitude_mm,
                    "direction_lps": None
                    if v.direction_lps is None
                    else list(v.direction_lps),
                    "direction_code": v.direction_code,
                    "anatomical_axes": list(rel.ANATOMICAL_AXES),
                    "anatomical_mm": None
                    if v.anatomical_mm is None
                    else list(v.anatomical_mm),
                    "anatomical_direction": None
                    if v.anatomical_direction is None
                    else list(v.anatomical_direction),
                    "orientation_code": v.orientation_code,
                    "normalized_displacement": None
                    if v.normalized_displacement is None
                    else list(v.normalized_displacement),
                    "normalized_distance": v.normalized_distance,
                }
                for (a, b), v in sorted(vectors.items())
            ],
            "pairs_unresolved": unresolved,
            "refinements": list(self.refinements),
            "uses": list(self.use_rows),
        }

    def summary(self, ideal: Ideal | None = None) -> dict:
        """What a series' record keeps of the map: the counts, the scale and which objects are complete, partial
        (with the orientations still lacking) or have no plane at all; the whole map is the study's file."""
        positions = self.positions()
        preds = self.predictions(ideal)
        return {
            "schema": "study_map_summary/v1",
            "knee": self.knee,
            "scale": {
                "mm": self.scale.mm,
                "source": self.scale.source,
                "code": self.scale.code,
            },
            "version": self.version,
            "complete": sorted(n for n, p in positions.items() if p.complete),
            "partial": {
                n: sorted(p.problems)
                for n, p in positions.items()
                if p.status == rel.PARTIAL
            },
            "predictions": sum(len(v) for v in preds.values()),
            "refinements": len(self.refinements),
            "uses": dict(self.uses),
        }
