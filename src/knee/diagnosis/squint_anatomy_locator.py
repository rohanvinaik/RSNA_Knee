"""Finite anatomy-first candidate selection for the production locator entrypoint."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from knee.diagnosis import squint_locator as shared
from knee.diagnosis.squint_geometry import (
    object_geometry,
    relative_scope_priors,
    window_scope_codes,
)


def locate_anatomy_first(
    study: dict, memory: dict, deadline: float | None = None
) -> dict:
    """Score only finite authored windows, then refine a bounded exact tie set."""
    cases = memory.get("cases", ())
    case_rows = (
        list(cases)
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes))
        else []
    )
    known = sorted(
        {
            row.get("subject")
            for row in case_rows
            if isinstance(row, Mapping)
            and isinstance(row.get("subject"), str)
            and not row["subject"].startswith("diagnosis/")
        }
    )
    declared = memory.get("objects", ())
    if isinstance(declared, Sequence) and not isinstance(declared, (str, bytes)):
        known.extend(
            name
            for name in declared
            if isinstance(name, str)
            and not name.startswith("diagnosis/")
            and name not in known
        )
    objects = {
        name: {
            "status": "unresolved_missing_reading",
            "profile": None,
            "candidate_profiles": [],
            "regions": [],
            "evidence": {"reason": "no_anatomical_windows_available"},
        }
        for name in known
    }
    series, series_uids = shared._profile_candidates(study)
    if not series:
        return {
            "outcome": "unresolved_missing_reading",
            "study_uid": study.get("study_uid"),
            "objects": objects,
            "evidence": {"series_uids": series_uids, "candidate_profiles_compared": 0},
        }
    bounds_by_series: dict[int, tuple[Any, Any, np.ndarray]] = {}
    foreground_by_series: dict[int, np.ndarray] = {}
    leg_bounds_lps = None
    foreground_prepared = False
    from knee.diagnosis.squint_profiles import profile_window

    raw_side = study.get("knee_side")
    knee_side = raw_side if raw_side in {"left", "right"} else None
    priorities = memory.get("object_order", ())
    priorities = (
        priorities
        if isinstance(priorities, Sequence) and not isinstance(priorities, (str, bytes))
        else ()
    )
    ordered = shared._object_order(
        known, priorities, {"femur", "tibia", "fibula", "patella"}
    )
    series_by_uid = {
        row.get("series_uid"): row
        for row in series
        if isinstance(row.get("series_uid"), str)
    }
    coarse_indexes = {id(row): shared._coarse_index(row) for row in series}
    geometry_by_subject: dict[str, dict[str, Any]] = {}
    exact_refinements = 0

    for subject in ordered:
        subject_refinement_start = exact_refinements
        if deadline is not None and time.monotonic() >= deadline:
            objects[subject]["evidence"] = {
                "reason": "deadline_before_search",
                "deadline_reached": True,
            }
            continue
        anchors = {
            name: item
            for name, item in geometry_by_subject.items()
            if name in {"femur", "tibia", "patella", "fibula"}
            and isinstance(item, Mapping)
            and isinstance(item.get("reference"), Mapping)
            and item["reference"].get("status") in {"complete", "partial"}
        }
        # The atlas scale is femoral breadth. A femur–tibia reference
        # separation is not that measurement, so authored spans remain
        # unscaled until a real breadth measurement is available.
        knee_scale_mm = None
        relative_priors = relative_scope_priors(
            subject,
            shared._anchor_names(subject, set(known)),
            case_rows,
            geometry_by_subject,
        )
        scope_evidence = []
        proposal_evidence = []
        scope_code_counts: dict[str, int] = {}
        view_costs: dict[str, dict[str, Any]] = {}
        coarse_by_view: dict[tuple[str, str, str] | None, list[dict[str, Any]]] = {}
        has_compatible_precedent = False

        for series_record in series:
            stack = series_record.get("stack")
            median = getattr(stack, "median", None)
            if (
                not isinstance(median, np.ndarray)
                or getattr(stack, "code", None) != "present"
            ):
                continue
            view = shared._view_key(series_record.get("view"))
            scoped, _examples, scope_name = shared._location_scope(
                case_rows, subject, view
            )
            scope_evidence.append(
                {
                    "view": None if view is None else list(view),
                    "source": scope_name,
                    "case_ids": [
                        row.get("case_id")
                        for row in scoped
                        if isinstance(row.get("case_id"), str)
                    ],
                }
            )
            compatible = [
                row
                for row in scoped
                if shared._source(row.get("profile")).get("procedure")
                == "knee.squint-profile/scan-tercile-v1"
            ]
            if not compatible:
                continue
            has_compatible_precedent = True
            if not foreground_prepared:
                bounds_by_series = {
                    id(row): shared._leg_bounds(row.get("stack"), row.get("leg_map"))
                    for row in series
                    if getattr(row.get("stack"), "code", None) == "present"
                    and isinstance(
                        getattr(row.get("stack"), "median", None), np.ndarray
                    )
                }
                foreground_by_series = {
                    key: value[2] for key, value in bounds_by_series.items()
                }
                leg_bounds_lps = shared._current_leg_frame_prior(
                    series, foreground_by_series
                )
                foreground_prepared = True
            foreground = foreground_by_series[id(series_record)]
            proposal = shared._anatomical_window_proposal(
                series_record,
                subject,
                leg_bounds_lps=leg_bounds_lps,
                foreground=foreground,
                anchors=anchors,
                knee_side=knee_side,
                knee_scale_mm=knee_scale_mm,
            )
            proposal_evidence.append(
                {
                    "series_uid": series_record.get("series_uid"),
                    "status": proposal.get("status"),
                    "reason": proposal.get("reason"),
                    "relative_scope_check": "direct_finite_candidate_scope_check",
                    "provenance": proposal.get("provenance", {}),
                    "window_count": len(proposal.get("windows", ())),
                }
            )
            windows = proposal.get("windows", ())
            view_id = json.dumps(view, separators=(",", ":"))
            cost = view_costs.setdefault(
                view_id,
                {
                    "view": None if view is None else list(view),
                    "windows_proposed": 0,
                    "windows_scored": 0,
                    "full_profiles_materialized": 0,
                    "relative_scope_check": "direct_finite_candidate_scope_check",
                    "anatomical_proposal_status": proposal.get("status", "unavailable"),
                },
            )
            cost.setdefault("proposal_sources", []).append(
                {
                    "series_uid": series_record.get("series_uid"),
                    "status": proposal.get("status", "unavailable"),
                    "relative_scope_check": "direct_finite_candidate_scope_check",
                }
            )
            cost["windows_proposed"] += len(windows)
            if not windows:
                continue
            scope_codes = window_scope_codes(series_record, windows, relative_priors)
            for code in scope_codes:
                scope_code_counts[code] = scope_code_counts.get(code, 0) + 1
            eligible = [
                window
                for window, code in zip(windows, scope_codes, strict=True)
                if code != "outside_anatomical_prior"
                and foreground[
                    window[0] : window[1], window[2] : window[3], window[4] : window[5]
                ].any()
            ]
            if not eligible:
                continue
            cost["windows_scored"] += len(eligible)
            names, integrals = coarse_indexes[id(series_record)]
            if not names:
                continue
            precedent_banks = [shared._banks(row.get("profile")) for row in compatible]
            case_vectors, case_masks = shared._case_coarse_matrix(
                compatible, names, precedent_banks
            )
            query_vectors, query_masks = shared._window_coarse_batch(
                names, integrals, eligible
            )
            scores = shared._coarse_case_scores_batch(
                query_vectors, query_masks, case_vectors, case_masks
            )
            rows = coarse_by_view.setdefault(view, [])
            for window, row_scores in zip(eligible, scores, strict=True):
                scored = [
                    (index, score)
                    for index, score in enumerate(row_scores)
                    if score is not None
                ]
                if not scored:
                    continue
                best = scored[0][1]
                for _index, score in scored[1:]:
                    if score[0] * best[1] > best[0] * score[1]:
                        best = score
                case_ids = sorted(
                    {
                        compatible[index].get("case_id")
                        for index, score in scored
                        if score[0] * best[1] == best[0] * score[1]
                        and isinstance(compatible[index].get("case_id"), str)
                    }
                )
                rows.append(
                    {
                        "window": tuple(window),
                        "series": series_record,
                        "coarse_score": best,
                        "case_ids": case_ids,
                        "centre_lps": shared._window_centre_lps(series_record, window),
                    }
                )

        exact_by_view: dict[tuple[str, str, str] | None, dict[str, Any]] = {}
        unresolved_coarse: dict[str, Any] = {}
        coarse_finalists: dict[str, Any] = {}
        case_best: dict[str, dict[str, Any]] = {}
        for view, candidates in coarse_by_view.items():
            if not candidates:
                continue
            best = candidates[0]["coarse_score"]
            for candidate in candidates[1:]:
                score = candidate["coarse_score"]
                if score[0] * best[1] > best[0] * score[1]:
                    best = score
            tied = [
                candidate
                for candidate in candidates
                if candidate["coarse_score"][0] * best[1]
                == best[0] * candidate["coarse_score"][1]
            ]
            view_id = json.dumps(view, separators=(",", ":"))
            coarse_finalists[view_id] = {
                "view": None if view is None else list(view),
                "candidate_count": len(tied),
                "coarse_best_squared_similarity": {
                    "numerator": str(best[0]),
                    "denominator": str(best[1]),
                },
                "candidates": [
                    {
                        "series_uid": item["series"].get("series_uid"),
                        "window": list(item["window"]),
                        "case_ids": item["case_ids"],
                        "centre_lps": item["centre_lps"],
                    }
                    for item in tied
                ],
            }
            if len(tied) > shared._MAX_EXACT_REFINEMENTS_PER_VIEW:
                unresolved_coarse[view_id] = {
                    "status": "unresolved_refinement_budget_exceeded",
                    "candidate_count": len(tied),
                    "max_exact_refinements": shared._MAX_EXACT_REFINEMENTS_PER_VIEW,
                    "coarse_best_squared_similarity": {
                        "numerator": str(best[0]),
                        "denominator": str(best[1]),
                    },
                    "candidates": coarse_finalists[view_id]["candidates"],
                }
                continue
            refined = []
            for candidate in tied:
                if deadline is not None and time.monotonic() >= deadline:
                    break
                series_record = candidate["series"]
                profile = profile_window(
                    dict(series_record), candidate["window"], subject=subject
                )
                query = shared._banks(profile)
                if query is None:
                    continue
                view_id = json.dumps(view, separators=(",", ":"))
                if view_id in view_costs:
                    view_costs[view_id]["full_profiles_materialized"] += 1
                scoped, _examples, _scope_name = shared._location_scope(
                    case_rows, subject, view
                )
                exact_cases = [
                    row
                    for row in scoped
                    if shared._source(row.get("profile")).get("procedure")
                    == shared._source(profile).get("procedure")
                ]
                banks = [shared._banks(row.get("profile")) for row in exact_cases]
                evidence = shared._batch_terms(
                    query, banks, compatible=[True] * len(exact_cases)
                )
                usable = [
                    (row, item)
                    for row, item in zip(exact_cases, evidence, strict=True)
                    if item is not None and item.get("code") == "ok"
                ]
                if not usable:
                    continue
                exact_best = usable[0][1]["cosine_squared"]
                for _row, item in usable[1:]:
                    score = item["cosine_squared"]
                    if score[0] * exact_best[1] > exact_best[0] * score[1]:
                        exact_best = score
                for source_case, item in usable:
                    case_id = source_case.get("case_id")
                    if not isinstance(case_id, str):
                        continue
                    score = item["cosine_squared"]
                    record = {
                        "profile": profile,
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate["window"],
                        "centre_lps": candidate["centre_lps"],
                    }
                    previous = case_best.get(case_id)
                    if (
                        previous is None
                        or score[0] * previous["score"][1]
                        > previous["score"][0] * score[1]
                    ):
                        case_best[case_id] = {"score": score, "items": [record]}
                    elif (
                        score[0] * previous["score"][1]
                        == previous["score"][0] * score[1]
                    ):
                        previous["items"].append(record)
                refined.append(
                    (
                        {
                            "subject": subject,
                            "window": candidate["window"],
                            "centre_lps": candidate["centre_lps"],
                            "profile": profile,
                        },
                        series_record,
                        exact_best,
                    )
                )
                exact_refinements += 1
            if not refined:
                continue
            exact_best = refined[0][2]
            for _candidate, _series_record, score in refined[1:]:
                if score[0] * exact_best[1] > exact_best[0] * score[1]:
                    exact_best = score
            exact_ties = [
                (item, row)
                for item, row, score in refined
                if score[0] * exact_best[1] == exact_best[0] * score[1]
            ]
            exact_by_view[view] = {"score": exact_best, "items": exact_ties}

        if not exact_by_view:
            objects[subject] = {
                "status": "unresolved_candidate_tie"
                if unresolved_coarse
                else "unresolved_missing_reading",
                "profile": None,
                "candidate_profiles": [],
                "regions": [],
                "evidence": {
                    "reason": "coarse_ties_exceed_refinement_budget"
                    if unresolved_coarse
                    else "no_compatible_anatomical_candidates"
                    if has_compatible_precedent
                    else "no_compatible_current_study_candidates",
                    "coarse_ties": unresolved_coarse,
                    "coarse_finalists": coarse_finalists,
                    "proposal_sources": proposal_evidence,
                    "location_precedent_scopes": scope_evidence,
                    "location_scope_codes": dict(sorted(scope_code_counts.items())),
                    "relative_scope_priors": relative_priors,
                    "candidate_costs_by_view": view_costs,
                    "leg_frame_prior": leg_bounds_lps is not None,
                },
            }
            continue
        candidate_profiles = []
        geometry_regions = []
        chosen_profiles = []
        for group in exact_by_view.values():
            for candidate, series_record in group["items"]:
                candidate_profiles.append(
                    {
                        "profile": candidate["profile"],
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window"),
                        "squared_similarity": {
                            "numerator": str(group["score"][0]),
                            "denominator": str(group["score"][1]),
                        },
                    }
                )
                geometry_regions.append(
                    {
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window"),
                    }
                )
            if len(group["items"]) == 1:
                chosen_profiles.append(group["items"][0][0]["profile"])
        spatial = object_geometry(subject, geometry_regions, series_by_uid)
        geometry_by_subject[subject] = spatial
        merged = None
        if chosen_profiles:
            try:
                from knee.diagnosis.squint_profiles import merge_profiles

                merged = merge_profiles(chosen_profiles, subject=subject)
            except (ImportError, ValueError):
                if len(chosen_profiles) == 1:
                    merged = chosen_profiles[0]
        best_candidates = [
            {
                "case_id": case_id,
                "squared_similarity": {
                    "numerator": str(row["score"][0]),
                    "denominator": str(row["score"][1]),
                },
                "candidates": row["items"],
            }
            for case_id, row in sorted(case_best.items())
        ]
        catalog = shared._intern_candidate_profiles(candidate_profiles, best_candidates)
        objects[subject] = {
            "status": "proposal",
            "profile": merged,
            "candidate_profiles": candidate_profiles,
            "regions": geometry_regions,
            "evidence": {
                "source": "current_study_anatomy_first_finite_windows",
                "candidate_view_count": len(exact_by_view),
                "selected_view_regions": len(chosen_profiles),
                "candidate_profiles_compared": exact_refinements
                - subject_refinement_start,
                "supporting_case_count": sum(
                    row.get("subject") == subject
                    for row in case_rows
                    if isinstance(row, Mapping)
                ),
                "location_scope_codes": dict(sorted(scope_code_counts.items())),
                "location_precedent_scopes": scope_evidence,
                "proposal_sources": proposal_evidence,
                "coarse_ties": unresolved_coarse,
                "coarse_finalists": coarse_finalists,
                "spatial_constraints": spatial,
                "relative_scope_priors": relative_priors,
                "anchor_reference_scope": "resolved_native_bone_references_only",
                "candidate_costs_by_view": view_costs,
                "case_best_candidates": best_candidates,
                "candidate_profile_catalog": catalog["profiles"],
                "candidate_bank_catalog": catalog["banks"],
                "candidate_series_context_catalog": catalog["series_contexts"],
                "patient_coordinates_carried": False,
                "leg_frame_prior": "measured_current_foreground_bounds_used_only_as_initial_reference_origin"
                if leg_bounds_lps is not None
                else "unavailable",
            },
        }
    return {
        "outcome": "located_with_proposals",
        "study_uid": study.get("study_uid"),
        "objects": objects,
        "evidence": {
            "series_uids": series_uids,
            "candidate_profiles_compared": exact_refinements,
            "candidate_generation": "finite_anatomy_first",
        },
    }
