"""Role-preserving exact composition of canonical objects from one case.

This layer copies existing rows into separate role slots. It neither diagnoses
an object nor creates joint/relationship observations from marginal counts.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from knee.diagnosis.models import Profile, Question
from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountLayout,
    _valid_bundle,
    _valid_layout,
)

__all__ = [
    "CompositionError",
    "PreparedComposition",
    "compose_question_profile",
    "prepare_composition",
]

_SCHEMA = "knee.diagnostic-composition/v1"


class CompositionError(ValueError):
    """Named invalid, incompatible, or contradictory composition input."""


def source_status_code(status: str, speaks: bool) -> str:
    """Name source conflicts and silence without interpreting medical state."""
    if status in ("conflicting", "mismatch", "malformed", "facet_mapping_conflict"):
        return "conflicting_source"
    if status in ("silent", "missing_source_object") and speaks:
        return "contradictory_source_status"
    if speaks:
        return "observed"
    return "silent"


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _pairs(value: object, field: str) -> dict[str, str]:
    if not isinstance(value, tuple):
        raise CompositionError(f"invalid_{field}")
    result: dict[str, str] = {}
    for pair in value:
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not _text(pair[0])
            or not isinstance(pair[1], str)
        ):
            raise CompositionError(f"invalid_{field}")
        key, item = pair
        if key in result:
            raise CompositionError(f"duplicate_{field}:{key}")
        result[key] = item
    return result


def _question_roles(question: Question) -> tuple[str, ...]:
    if not isinstance(question, Question) or not _text(question.question_id):
        raise CompositionError("invalid_question")
    if question.subject != "diagnosis/" + question.question_id:
        raise CompositionError("invalid_question_subject")
    for field in ("objects", "banks", "bank_prefixes", "context_keys"):
        values = getattr(question, field)
        if (
            not isinstance(values, tuple)
            or any(not _text(value) for value in values)
            or len(set(values)) != len(values)
        ):
            raise CompositionError(f"invalid_question_{field}")
    if not question.objects or any("/" in role for role in question.objects):
        raise CompositionError("invalid_question_objects")
    return question.objects


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _layout_record(layout: CountLayout) -> dict:
    return {
        "layout_id": layout.layout_id,
        "carrier_id": layout.carrier_id,
        "banks": [[bank.name, bank.row_count] for bank in layout.banks],
    }


def _source_scope(profile: Profile, provenance: Mapping[str, str]) -> str:
    scope = profile.scope
    subject_object_scope = f"object:{profile.subject}"
    if scope == subject_object_scope:
        return scope
    if scope.startswith(subject_object_scope + ";composition:"):
        fingerprint = scope[len(subject_object_scope + ";composition:") :]
        declared = provenance.get("layout_fingerprint")
        layout_identity_parts = profile.bundle.layout.layout_id.split(":")
        if (
            not _text(fingerprint)
            or declared != fingerprint
            or fingerprint not in layout_identity_parts
        ):
            raise CompositionError(f"incompatible_scope_identity:{profile.subject}")
        return scope
    if scope.startswith("region:") and _text(scope[len("region:") :]):
        return scope
    raise CompositionError(f"incompatible_scope:{profile.subject}")


def _profile_metadata(profile: Profile) -> tuple[dict, dict, dict, str]:
    if not _valid_bundle(profile.bundle):
        raise CompositionError(f"invalid_bundle:{profile.subject}")
    if not _text(profile.mode) or not _text(profile.source_id):
        raise CompositionError(f"invalid_source:{profile.subject}")
    context = _pairs(profile.context, "context")
    provenance = _pairs(profile.provenance, "provenance")
    statuses = _pairs(profile.bank_statuses, "bank_statuses")
    source_scope = _source_scope(profile, provenance)
    banks = {bank.name for bank in profile.bundle.layout.banks}
    if set(statuses) - banks:
        raise CompositionError(f"unknown_status_bank:{profile.subject}")
    for bank, counts in zip(
        profile.bundle.layout.banks, profile.bundle.counts, strict=True
    ):
        status = statuses.get(bank.name, "")
        if bank.name in statuses and not _text(status):
            raise CompositionError(f"invalid_bank_status:{bank.name}")
        code = source_status_code(status, any(counts))
        if code in ("conflicting_source", "contradictory_source_status"):
            raise CompositionError(f"{code}:{profile.subject}:{bank.name}")
    for field in ("status", "preparation_status", "assembly_status"):
        if source_status_code(provenance.get(field, ""), False) == "conflicting_source":
            raise CompositionError(f"conflicting_source:{profile.subject}:{field}")
    for field in ("study_uid", "source_state", "split", "source_group"):
        if (
            field in context
            and field in provenance
            and context[field] != provenance[field]
        ):
            raise CompositionError(f"contradictory_source:{profile.subject}:{field}")
    return context, provenance, statuses, source_scope


def _case_metadata(
    selected: Sequence[Profile], metadata: Mapping[str, tuple], question: Question
) -> tuple[str, dict, dict]:
    modes = {profile.mode for profile in selected}
    if len(modes) != 1:
        raise CompositionError("incompatible_modes")
    common: dict[str, str] = {}
    source: dict[str, str] = {}
    contexts = [metadata[p.subject][0] for p in selected]
    for field in ("study_uid", "source_state"):
        values = [
            metadata[p.subject][0].get(field, metadata[p.subject][1].get(field))
            for p in selected
        ]
        declared = {value for value in values if value is not None}
        if len(declared) > 1:
            raise CompositionError(f"contradictory_source:{field}")
        if declared:
            if any(value is None or not _text(value) for value in values):
                raise CompositionError(f"missing_source_identity:{field}")
            source[field] = next(iter(declared))
    for field in ("split", "source_group"):
        values = [
            metadata[p.subject][0].get(field, metadata[p.subject][1].get(field))
            for p in selected
        ]
        declared = {value for value in values if _text(value)}
        if len(declared) > 1:
            raise CompositionError(f"contradictory_source:{field}")
        if declared:
            source[field] = next(iter(declared))
    for key in question.context_keys:
        values = {context[key] for context in contexts if key in context}
        if len(values) > 1:
            raise CompositionError(f"incompatible_context:{key}")
        if all(key in context for context in contexts):
            common[key] = next(iter(values))
    ids = {profile.source_id for profile in selected}
    if len(ids) == 1:
        source_id = next(iter(ids))
    elif "study_uid" in source:
        source_id = "study:" + source["study_uid"]
    else:
        raise CompositionError("different_cases_or_undeclared_case_identity")
    return source_id, common, source


class PreparedComposition:
    """Reusable, run-scoped layout and zero-row preparation for one question."""

    __slots__ = ("_layout_cache", "_zero_rows", "question", "source_layouts")

    def __init__(
        self, question: Question, source_layouts: Mapping[str, CountLayout]
    ) -> None:
        roles = _question_roles(question)
        if not isinstance(source_layouts, Mapping) or set(source_layouts) != set(roles):
            raise CompositionError("invalid_source_layouts")
        layouts = dict(source_layouts)
        if any(not _valid_layout(layout) for layout in layouts.values()):
            raise CompositionError("invalid_source_layouts")
        if len({layout.carrier_id for layout in layouts.values()}) != 1:
            raise CompositionError("incompatible_carriers")
        declared_layouts: dict[str, CountLayout] = {}
        for layout in layouts.values():
            previous = declared_layouts.setdefault(layout.layout_id, layout)
            if previous != layout:
                raise CompositionError("contradictory_layout_identity")
        if len({layout.banks for layout in layouts.values()}) != 1:
            raise CompositionError("contradictory_carrier_banks")
        self.question = question
        self.source_layouts = layouts
        self._layout_cache: dict[str, CountLayout] = {}
        self._zero_rows: dict[int, tuple[int, ...]] = {}

    def compose(self, profiles: Sequence[Profile]) -> Profile:
        """Compose another case under these frozen declarations."""
        return compose_question_profile(
            profiles,
            self.question,
            source_layouts=self.source_layouts,
            _prepared=self,
        )


def prepare_composition(
    question: Question, source_layouts: Mapping[str, CountLayout]
) -> PreparedComposition:
    """Prepare immutable role layouts and zero rows for a bounded run lifetime."""
    return PreparedComposition(question, source_layouts)


def compose_question_profile(
    profiles: Sequence[Profile],
    question: Question,
    *,
    source_layouts: Mapping[str, CountLayout] | None = None,
    _prepared: PreparedComposition | None = None,
) -> Profile:
    """Bundle ONE case under deterministic object/<role>/<original-bank> slots.

    Without a template every declared role must be supplied. With a complete
    ``source_layouts`` mapping, missing roles get exact zero rows and explicit
    missing_source_object statuses under the same layout as a complete case.
    Present layouts must match their template exactly, including references and
    optional banks. Zero rows are silence, never a diagnosis of normality.

    Inputs must have the declared canonical subject and an explicit object or
    region scope. Product composition scopes require matching provenance and
    count-layout fingerprints. Different per-role references and scopes are
    retained, not rewritten to match; a changed declaration changes identity.
    This count-only carrier is
    the direct sum of the original per-role carrier spaces; its provenance names
    every source layout so no canonical encoder or row basis is changed.
    """
    roles = _question_roles(question)
    if _prepared is not None:
        if _prepared.question != question:
            raise CompositionError("prepared_question_mismatch")
        if (
            source_layouts is not None
            and dict(source_layouts) != _prepared.source_layouts
        ):
            raise CompositionError("prepared_layout_mismatch")
        source_layouts = _prepared.source_layouts
    if not isinstance(profiles, Sequence) or isinstance(profiles, (str, bytes)):
        raise CompositionError("invalid_profiles")
    by_role: dict[str, Profile] = {}
    metadata: dict[str, tuple] = {}
    for profile in profiles:
        if not isinstance(profile, Profile) or not _text(profile.subject):
            raise CompositionError("invalid_profile")
        if profile.subject not in roles:
            continue
        if profile.subject in by_role:
            raise CompositionError(f"duplicate_object:{profile.subject}")
        metadata[profile.subject] = _profile_metadata(profile)
        by_role[profile.subject] = profile
    if not by_role:
        raise CompositionError("no_source_profiles")
    if source_layouts is None:
        missing = tuple(role for role in roles if role not in by_role)
        if missing:
            raise CompositionError("source_layouts_required:" + ",".join(missing))
        layouts = {role: by_role[role].bundle.layout for role in roles}
    else:
        if not isinstance(source_layouts, Mapping) or set(source_layouts) != set(roles):
            raise CompositionError("invalid_source_layouts")
        layouts = dict(source_layouts)
        if any(not _valid_layout(layout) for layout in layouts.values()):
            raise CompositionError("invalid_source_layouts")
        for role, profile in by_role.items():
            if profile.bundle.layout != layouts[role]:
                raise CompositionError(f"incompatible_source_layout:{role}")
    if len({layout.carrier_id for layout in layouts.values()}) != 1:
        raise CompositionError("incompatible_carriers")
    declared_layouts: dict[str, CountLayout] = {}
    for layout in layouts.values():
        previous = declared_layouts.setdefault(layout.layout_id, layout)
        if previous != layout:
            raise CompositionError("contradictory_layout_identity")
    if len({layout.banks for layout in layouts.values()}) != 1:
        raise CompositionError("contradictory_carrier_banks")
    selected = tuple(by_role[role] for role in roles if role in by_role)
    source_id, common_context, source = _case_metadata(selected, metadata, question)
    mode = selected[0].mode
    declarations = [[role, _layout_record(layouts[role])] for role in roles]
    # Plain object scopes are already bound to their role. Product composition
    # and region scopes carry additional source identity and enter the layout
    # identity verbatim. A missing plain-object role must not change the layout
    # merely because its observation is absent.
    scopes = [
        [role, metadata[role][3]]
        for role in roles
        if role in metadata and metadata[role][3] != f"object:{role}"
    ]
    carrier_record = [
        [
            role,
            layouts[role].carrier_id,
            [[b.name, b.row_count] for b in layouts[role].banks],
        ]
        for role in roles
    ]
    identity = {
        "schema": _SCHEMA,
        "question": [question.question_id, question.subject, list(roles)],
        "context_keys": list(question.context_keys),
        "sources": declarations,
        "mode": mode,
        "scopes": scopes,
    }
    counts: list[tuple[int, ...]] = []
    statuses: list[tuple[str, str]] = []
    provenance = [
        ("composition_schema", _SCHEMA),
        ("source_layouts", _json(declarations)),
        (
            "source_state_compatibility",
            "declared_agreement" if "source_state" in source else "undeclared",
        ),
        (
            "case_compatibility",
            "shared_study_uid" if "study_uid" in source else "shared_source_id",
        ),
    ]
    provenance.extend(sorted(source.items()))
    zero_rows = _prepared._zero_rows if _prepared is not None else {}
    layout_cache = _prepared._layout_cache if _prepared is not None else {}
    composite_layout_id = _SCHEMA + ":" + _digest(identity)
    layout = layout_cache.get(composite_layout_id)
    if layout is None:
        layout = CountLayout(
            composite_layout_id,
            "knee.role-direct-sum-carrier/v1:" + _digest(carrier_record),
            tuple(
                BankLayout(f"object/{role}/{bank.name}", bank.row_count)
                for role in roles
                for bank in layouts[role].banks
            ),
        )
        layout_cache[composite_layout_id] = layout
    for role in roles:
        prefix = f"object/{role}/"
        profile = by_role.get(role)
        if profile is None:
            provenance.append((prefix + "availability", "missing_source_object"))
        else:
            context, original_provenance, source_statuses, original_scope = metadata[
                role
            ]
            provenance.extend(
                (
                    (prefix + "source_id", profile.source_id),
                    (prefix + "scope", original_scope),
                    (prefix + "context", _json(context)),
                    (prefix + "provenance", _json(original_provenance)),
                    (
                        prefix + "availability",
                        "available"
                        if any(any(row) for row in profile.bundle.counts)
                        else "silent",
                    ),
                )
            )
            provenance.extend(
                (prefix + key, value) for key, value in sorted(context.items())
            )
            provenance.extend(
                (prefix + "provenance/" + key, value)
                for key, value in sorted(original_provenance.items())
            )
        for index, bank in enumerate(layouts[role].banks):
            name = prefix + bank.name
            row = (
                profile.bundle.counts[index]
                if profile is not None
                else zero_rows.setdefault(bank.row_count, (0,) * bank.row_count)
            )
            counts.append(row)
            status = (
                "missing_source_object"
                if profile is None
                else source_statuses.get(
                    bank.name, "observed" if any(row) else "silent"
                )
            )
            statuses.append((name, status))
    missing_context = tuple(
        key for key in question.context_keys if not _text(common_context.get(key))
    )
    provenance.append(
        (
            "context_compatibility",
            "missing:" + ",".join(missing_context) if missing_context else "compatible",
        )
    )
    return Profile(
        question.subject,
        CountBundle(layout, tuple(counts)),
        mode,
        "question:" + question.question_id,
        source_id,
        tuple(sorted(common_context.items())),
        tuple(statuses),
        tuple(provenance),
    )
