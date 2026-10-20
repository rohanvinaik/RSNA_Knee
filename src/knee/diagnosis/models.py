"""Frozen exchange records for individual diagnostic case memory.

Observed bundles and independently sourced calls are distinct fields. No object
is a class prototype. Exact count/carrier semantics come from knee.encoding.
"""

from dataclasses import dataclass

from knee.encoding.counts import CountBundle


@dataclass(frozen=True, slots=True)
class Profile:
    subject: str
    bundle: CountBundle
    mode: str
    scope: str
    source_id: str
    context: tuple[tuple[str, str], ...] = ()
    bank_statuses: tuple[tuple[str, str], ...] = ()
    provenance: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Call:
    question: str
    digit: int
    source: str
    words: str = ""


@dataclass(frozen=True, slots=True)
class Case:
    case_id: str
    study_uid: str
    profile: Profile
    calls: tuple[Call, ...]
    teaching_revision: str


@dataclass(frozen=True, slots=True)
class Question:
    question_id: str
    subject: str
    objects: tuple[str, ...]
    banks: tuple[str, ...] = ()
    bank_prefixes: tuple[str, ...] = ()
    context_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Trust:
    case_id: str
    question: str
    numerator: int
    denominator: int
    source: str


@dataclass(frozen=True, slots=True)
class Censor:
    censor_id: str
    question: str
    answer: int
    profile: Profile
    numerator: int
    denominator: int
    source: str


@dataclass(frozen=True, slots=True)
class Snapshot:
    revision: str
    cases: tuple[Case, ...] = ()
    trust: tuple[Trust, ...] = ()
    censors: tuple[Censor, ...] = ()
    schema_version: str = "knee.diagnostic-memory/v1"
