"""II.7 — deterministic multilingual report -> 12-label oracle (train-only).

The weak-supervision problem closes symbolically: a lexicon + negation +
laterality parser derives pseudo-labels for the 4,349 unlabeled training
studies. Nothing at test time depends on this (reports are train-only).

Languages (census 2026-08-29 over all 4,407 reports): en 1729, es 674,
tr 546, hr/sr-latin 385, el 321, nl/de 253, bg/sr-cyrillic 220, fr/it/pt in
the tail. The 58 explicitly-labeled studies span all groups and are the
parser's gold validation gate.

Mechanics (all deterministic):
- script + marker-word language detection (pure, pinnable)
- per-finding multilingual term lists (authored MSK lexicon; laterality is
  IN the terms — "menisco interno" vs "menisco externo")
- negation by sentence-scoped windows: negator BEFORE the term for most
  languages; Turkish negates POSTPOSED ("efüzyon izlenmedi"), so tr also
  scans a window AFTER the term
- a finding is 1 iff some sentence contains a non-negated term; else 0

Codes over booleans where a decision can be indeterminate; the parser
never silently guesses on unsupported text (label "no_terms_found" studies
are reported, not folded into negatives blindly — the caller decides).
"""

from __future__ import annotations

import re
import unicodedata

FINDINGS = [
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
]

# ---------------------------------------------------------------- language --

_TR_MARKERS = [
    "menisküs",
    "çapraz bağ",
    " diz",
    "izlenmedi",
    "saptanmadı",
    "efüzyon",
    "kırık",
]
_ES_MARKERS = [
    " rodilla",
    "menisco interno",
    "menisco externo",
    "derrame",
    "hallazgos",
    "impresión",
    "rotura",
]
_NL_MARKERS = ["kruisband", "bevindingen", "geen ", "meniscus", " knie", "conclusie"]
_DE_MARKERS = ["kreuzband", "erguss", "kein ", "befund", "innenmeniskus", "beurteilung"]
_FR_MARKERS = ["genou", "épanchement", "ménisque", "pas de", "croisé"]
_HR_MARKERS = [
    "koljena",
    "zgloba",
    "hrskavic",
    "menisk",
    "izljev",
    "nema ",
    "uredna",
    "prati se",
]
_IT_MARKERS = ["ginocchio", "versamento", "legamento", "menisco mediale", "reperti"]
_PT_MARKERS = [" joelho", "ruptura", "achados", "derrame articular"]


def detect_language(text: str) -> str:
    """Deterministic language code for a report (script first, then markers)."""
    if sum(1 for c in text if "Ѐ" <= c <= "ӿ") > 20:
        return "cyr"
    if sum(1 for c in text if "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῾") > 20:
        return "el"
    lo = " " + text.lower() + " "
    scores = {
        "tr": sum(m in lo for m in _TR_MARKERS),
        "es": sum(m in lo for m in _ES_MARKERS),
        "nl": sum(m in lo for m in _NL_MARKERS),
        "de": sum(m in lo for m in _DE_MARKERS),
        "fr": sum(m in lo for m in _FR_MARKERS),
        "hr": sum(m in lo for m in _HR_MARKERS),
        "it": sum(m in lo for m in _IT_MARKERS),
        "pt": sum(m in lo for m in _PT_MARKERS),
    }
    best = max(scores, key=lambda k: scores[k])
    if scores[best] >= 2:
        return best
    return "en"  # english is the plurality default for latin-script residue


# ----------------------------------------------------------------- lexicon --
# Terms are matched on accent-stripped lowercase for latin scripts; Greek and
# Cyrillic terms are matched in native script (also lowercased/accent-folded).

LEXICON: dict = {
    "ACL": [
        "acl",
        "anterior cruciate",
        "ligamento cruzado anterior",
        "lca",
        "voorste kruisband",
        "vkb",
        "vorderes kreuzband",
        "vordere kreuzband",
        "vkl",
        "acl-",
        " kruisbandletsel",
        "ligament croise anterieur",
        "on capraz bag",
        "ocb",
        "prosthios chiastos",
        "προσθιος χιαστος",
        "προσθιου χιαστου",
        "предна кръстна",
        "предната кръстна",
        "prednja ukrizena",
        "prednjeg ukrizenog",
        "prednja ukrstena",
        "lig. crociato anteriore",
        "legamento crociato anteriore",
    ],
    "MCL": [
        "mcl",
        "medial collateral",
        "ligamento colateral medial",
        "ligamento colateral interno",
        "ligamento lateral interno",
        "mediale collaterale band",
        "mediale band",
        "innenband",
        "ligament collateral medial",
        "ligament lateral interne",
        "ic yan bag",
        "medial kollateral",
        "εσω πλαγιος συνδεσμος",
        "εσω πλαγιου συνδεσμου",
        "вътрешна колатерална",
        "медиална колатерална",
        "medijalni kolateralni",
        "legamento collaterale mediale",
    ],
    "Medial Meniscus": [
        "medial meniscus",
        "menisco interno",
        "menisco medial",
        "mediale meniscus",
        "binnenmeniscus",
        "innenmeniskus",
        "menisque interne",
        "menisque medial",
        "ic menisk",
        "medial menisk",
        "εσω μηνισκος",
        "εσω μηνισκου",
        "медиалния мениск",
        "вътрешния мениск",
        "медиален мениск",
        "medijalni menisk",
        "unutarnji menisk",
        "menisco mediale",
        "menisco interno y",
        "medial and lateral menisc",
        "both menisci",
        "ambos meniscos",
        "oba meniska",
        "beide menisci",
        "beide menisken",
    ],
    "Lateral Meniscus": [
        "lateral meniscus",
        "menisco externo",
        "menisco lateral",
        "laterale meniscus",
        "buitenmeniscus",
        "aussenmeniskus",
        "menisque externe",
        "menisque lateral",
        "dis menisk",
        "lateral menisk",
        "εξω μηνισκος",
        "εξω μηνισκου",
        "латералния мениск",
        "външния мениск",
        "латерален мениск",
        "lateralni menisk",
        "vanjski menisk",
        "menisco laterale",
        "interno y lateral",
        "interno y externo",
        "medial and lateral menisc",
        "both menisci",
        "ambos meniscos",
        "oba meniska",
        "beide menisci",
        "beide menisken",
    ],
    "Medial OA": [
        "medial compartment osteoarthr",
        "medial osteoarthr",
        "medial joint space narrow",
        "artrosis femorotibial medial",
        "artrosis femorotibial interna",
        "gonartrosis medial",
        "artrosis del compartimento interno",
        "mediale gonartrose",
        "gonartrose mediaal",
        "mediale gonarthrose",
        "gonarthrose medial",
        "femoro-tibiale interne",
        "medial gonartroz",
        "medial kompartman",
        "ic kompartman",
        "εσω διαμερισμα",
        "εσω μηροκνημιαι",
        "медиална гонартроза",
        "медиалния кондил артроз",
        "medijalnom kompartmentu",
        "medijalnog kompartmenta",
        "gonartrosi mediale",
    ],
    "Lateral OA": [
        "lateral compartment osteoarthr",
        "lateral osteoarthr",
        "lateral joint space narrow",
        "artrosis femorotibial lateral",
        "artrosis femorotibial externa",
        "gonartrosis lateral",
        "artrosis del compartimento externo",
        "laterale gonartrose",
        "gonartrose lateraal",
        "laterale gonarthrose",
        "gonarthrose lateral",
        "femoro-tibiale externe",
        "lateral gonartroz",
        "lateral kompartman",
        "dis kompartman",
        "εξω διαμερισμα",
        "εξω μηροκνημιαι",
        "латерална гонартроза",
        "lateralnom kompartmentu",
        "lateralnog kompartmenta",
        "gonartrosi laterale",
    ],
    "PF OA": [
        "patellofemoral osteoarthr",
        "patellofemoral arthr",
        "patellofemoral compartment",
        "retropatellar",
        "chondromalacia patell",
        "condromalacia rotuli",
        "condromalacia patelar",
        "artrosis femoropatelar",
        "femoropatelar",
        "patellofemorale artrose",
        "retropatellararthrose",
        "femoropatellararthrose",
        "femoro-patellaire",
        "patellofemoral artroz",
        "patellofemoral kondromalazi",
        "kondromalazi patell",
        "επιγονατιδομηριαι",
        "пателофеморална",
        "patelofemoralna",
        "femoro-rotulea",
        "femororotulea",
    ],
    "Effusion": [
        "effusion",
        "joint fluid",
        "hydrops",
        "derrame",
        "liquido articular aumentado",
        "gewrichtsvocht",
        "vochtcollectie",
        "hydrops",
        "erguss",
        "gelenkserguss",
        "gelenkerguss",
        "epanchement",
        "efuzyon",
        "eklem sivisi artis",
        "eklem sivisinda artis",
        "eklem ici sivi",
        "συλλογη υγρου",
        "υδραρθρο",
        "ενδαρθρικη συλλογη",
        "ставен излив",
        "излив",
        "izljev",
        "efuzija",
        "versamento",
    ],
    "Synovitis": [
        "synovitis",
        "synovial thickening",
        "sinovitis",
        "synoviale verdikking",
        "synovialitis",
        "synovite",
        "sinovit",
        "υμενιτιδα",
        "συνοβιτιδα",
        "синовит",
        "sinovitis",
        "sinovite",
        "synovitida",
    ],
    "Baker's": [
        "baker",
        "popliteal cyst",
        "quiste popliteo",
        "cyste van baker",
        "poplitea cyste",
        "baker-zyste",
        "bakerzyste",
        "kyste poplite",
        "baker kisti",
        "popliteal kist",
        "κυστη baker",
        "ιγνυακη κυστη",
        "киста на бейкър",
        "бейкерова киста",
        "бейкър",
        "bakerova cista",
        "poplitealna cista",
        "cisti di baker",
        "cisti poplitea",
    ],
    "Contusion": [
        "contusion",
        "bone bruise",
        "bone marrow edema",
        "bone marrow oedema",
        "marrow edema",
        "contusion osea",
        "edema oseo",
        "edema de medula osea",
        "botcontusie",
        "beenmergoedeem",
        "knochenmarkodem",
        "bone bruise",
        "contusion osseuse",
        "oedeme osseux",
        "kemik iligi odemi",
        "kontuzyon",
        "οστικο οιδημα",
        "οιδημα μυελου",
        "костномозъчен едем",
        "контузия",
        "koštani edem",
        "kostani edem",
        "edem kostne srzi",
        "edema osseo",
        "contusione",
    ],
    "Fracture": [
        "fracture",
        "fractura",
        "fractuur",
        "fraktur",
        "frakture",
        "fraktür",
        "kirik",
        "καταγμα",
        "фрактура",
        "счупване",
        "fraktura",
        "prijelom",
        "frattura",
        "fratura",
    ],
}

# ---------------------------------------------------------------- negation --

NEGATORS_PRE: dict = {
    "en": [
        "no ",
        "without ",
        "no evidence",
        "intact",
        "unremarkable",
        "normal ",
        "negative for",
        "rather than",
        "rule out",
        "r/o",
        "not ",
    ],
    "es": [
        "no ",
        "sin ",
        "no se observa",
        "no se aprecia",
        "no se identifica",
        "conservado",
        "integro",
        "integra",
        "normal",
        "descarta",
    ],
    "nl": ["geen ", "zonder ", "intact", "intacte", "normaal", "normale", "gaaf"],
    "de": ["kein", "ohne ", "unauffallig", "intakt", "regelrecht", "kein nachweis"],
    "fr": [
        "pas de",
        "pas d'",
        "sans ",
        "absence de",
        "absence d'",
        "intact",
        "integre",
    ],
    "hr": [
        "bez ",
        "nema ",
        "uredna",
        "uredan",
        "urednog",
        "ne prati se",
        "nije",
        "ne vidi se",
        "očuvan",
        "ocuvan",
    ],
    "it": ["non ", "senza ", "assenza di", "nella norma", "integro", "regolare"],
    "pt": ["sem ", "nao ", "não ", "normal", "integro", "preservado"],
    "el": ["χωρις", "δεν ", "ανευ", "φυσιολογικ", "ακεραι", "αρνητικ"],
    "cyr": [
        "без ",
        "не се",
        "липсва",
        "липсват",
        "не установ",
        "нормал",
        "запазен",
        "запазена",
        "интактн",
        "не са",
    ],
    "tr": ["izlenmeyen", "olmayan"],
}

NEGATORS_POST: dict = {
    # Turkish negates after the noun phrase; a few analogues elsewhere
    "tr": [
        "izlenmedi",
        "izlenmemistir",
        "saptanmadi",
        "saptanmamistir",
        "gorulmedi",
        "gozlenmedi",
        "normaldir",
        "dogaldir",
        "intakttir",
        "yoktur",
        "mevcut degildir",
        "izlenmemektedir",
        "tabiidir",
        "olagandir",
    ],
    "en": [
        "is intact",
        "are intact",
        "is normal",
        "are normal",
        "is unremarkable",
        "within normal limits",
        "not seen",
        "not identified",
        "not demonstrated",
        "without tear",
        "no tear",
        "without evidence",
    ],
    "es": [
        "conservado",
        "conservada",
        "sin alteraciones",
        "de aspecto normal",
        "sin evidencia de rotura",
        "normal",
    ],
    "nl": ["intact", "normaal", "zonder afwijkingen", "niet aangetoond"],
    "de": ["unauffallig", "intakt", "regelrecht", "ohne befund"],
    "fr": ["intact", "sans anomalie", "normal", "normale"],
    "hr": [
        "uredna",
        "uredan",
        "urednog izgleda",
        "bez patoloskih promjena",
        "nije vidljiv",
        "ocuvan",
        "bez znakova",
        "primjerenih intenziteta",
        "odrzanog kontinuiteta",
        "bez rupture",
    ],
    "it": ["integro", "nella norma", "regolare", "non evidente"],
    "pt": ["preservado", "normal", "sem alteracoes"],
    "el": [
        "φυσιολογικ",
        "ακεραι",
        "χωρις παθολογια",
        "δεν αναδεικνυεται",
        "δεν παρατηρειται",
        "ελεγχεται εντος του φυσιολογικου",
        "ελεγχεται φυσιολογικ",
        "ελεγχεται ακεραι",
    ],
    "cyr": [
        "е запазен",
        "са запазени",
        "без промени",
        "не се установ",
        "нормална структура",
        "неangepromenjena",
        "непроменена",
    ],
}

# Findings whose label is a structure x pathology CONJUNCTION (gold gate
# 2026-08-29: mere mention or degeneration of a ligament/meniscus is 0; the
# label asserts an INJURY — tear/rupture words in the same sentence).
TEAR_WORDS = [
    "tear",
    "torn",
    "rupture",
    "ruptur",
    "riss",
    "ruptuur",
    "scheur",
    "rotura",
    "desgarro",
    "yirtik",
    "ruptur",
    "ριξη",
    "ρηξη",
    "руптура",
    "разкъсване",
    "лезия на",
    "ruptura",
    "lezija",
    "rottura",
    "distorsion",
    "sprain",
    "avulsion",
    "discontinu",
    "diskontinu",
]
DEGEN_WORDS = [
    "osteoarthr",
    "arthros",
    "artros",
    "gonarthr",
    "gonartroz",
    "gonartros",
    "артроз",
    "гонартроз",
    "αρθρωσ",
    "οστεοαρθρ",
    "chondropath",
    "condropat",
    "kondropat",
    "hondropat",
    "χονδροπαθ",
    "хондропат",
    "chondromala",
    "condromala",
    "kondromala",
    "χονδρομαλ",
    "osteophyt",
    "osteofit",
    "остеофит",
    "οστεοφυτ",
    "degenerative chang",
    "cartilage thinning",
    "cartilage loss",
    "denudation",
    "denudacij",
    "joint space narrow",
    "изтън",
    "λεπτυνση",
    "incelme",
    "verschmaler",
    "chondral defect",
    "cartilage defect",
    "knorpelschaden",
    "kraakbeenverlies",
    "usura",
]
MEDIAL_WORDS = [
    "medial",
    "interno",
    "interna",
    "interne",
    "ic ",
    "εσω",
    "медиал",
    "вътрешн",
    "medijaln",
    "unutar",
    "mediaal",
    "binnen",
    "innen",
]
LATERAL_WORDS = [
    "lateral",
    "externo",
    "externa",
    "externe",
    "dis ",
    "εξω",
    "латерал",
    "външн",
    "lateraln",
    "vanjsk",
    "lateraal",
    "buiten",
    "aussen",
]
PF_WORDS = [
    "patell",
    "rotul",
    "retropatel",
    "femoropatel",
    "patelofemoral",
    "epigonatid",
    "επιγονατιδ",
    "пател",
    "kniescheibe",
    "kneecap",
]

CONJUNCTIONS = {
    "ACL": ("ACL", TEAR_WORDS),
    "MCL": ("MCL", TEAR_WORDS),
    "Medial Meniscus": ("Medial Meniscus", TEAR_WORDS),
    "Lateral Meniscus": ("Lateral Meniscus", TEAR_WORDS),
}

SMALLNESS_WORDS = [
    # minimal/trace tier ONLY — gold counts small-to-moderate effusions
    "minimal",
    "trace",
    "scant",
    "tiny",
    "minimo",
    "minima",
    "escaso",
    "escasa",
    "spoor",
    "minimaln",
    "ελαχιστ",
    "минимал",
    "minimal duzeyde",
    "minime",
    "esiguo",
]
REACTIVE_EDEMA_CONTEXT = [
    "subchondral",
    "subcondral",
    "subhondral",
    "subkondral",
    "субхондрал",
    "υποχονδρι",
    "reactive",
    "reactivo",
    "reaktiv",
    "degenerat",
    "artros",
    "arthros",
    "osteoarthr",
    "gonartro",
    "артроз",
    "αρθρωσ",
]

_PRE_WINDOW = 60  # chars before the term, clipped at sentence start
_POST_WINDOW = 90  # chars after the term, clipped at sentence end


def normalize(text: str) -> str:
    """Lowercase + strip latin accents (native scripts pass through).

    Turkish dotted/dotless i both fold to plain i via NFD stripping after
    casefold, which is what the lexicon spellings assume.
    """
    text = text.replace("\u00b5", "\u03bc")  # micro sign -> greek mu (Word artifact)
    text = text.casefold()
    out = []
    for ch in unicodedata.normalize("NFD", text):
        cat = unicodedata.category(ch)
        if cat == "Mn":  # combining accent
            continue
        out.append(ch)
    return "".join(out)


def split_sentences(text: str) -> list:
    """Deterministic sentence split on ./;/! /? and newlines (keeps order)."""
    parts = re.split(r"[.;!?\n\r]+", text)
    return [p.strip() for p in parts if p.strip()]


def term_negated(sentence: str, term_start: int, term_end: int, lang: str) -> str:
    """Decide whether a term occurrence is negated within its sentence.

    Named codes: "negated" / "asserted". Pre-window negators (most
    languages) look back from the term; post-window negators (tr and
    verb-final constructions elsewhere) look forward.
    """
    pre = sentence[max(0, term_start - _PRE_WINDOW) : term_start]
    for neg in NEGATORS_PRE.get(lang, []) + NEGATORS_PRE["en"]:
        if neg in pre:
            return "negated"
    post = sentence[term_end : term_end + _POST_WINDOW]
    for neg in NEGATORS_POST.get(lang, []):
        if neg in post:
            return "negated"
    return "asserted"


def parse_report(text: str) -> dict:
    """Parse one report into 12 labels + provenance.

    Returns {"labels": {finding: 0|1}, "language": code,
             "hits": {finding: [asserted sentence snippets]},
             "coverage": "terms_found" | "no_terms_found"}.
    A finding is 1 iff at least one sentence asserts one of its terms.
    """
    lang = detect_language(text)
    norm_sentences = [normalize(s) for s in split_sentences(text)]
    labels = {}
    hits: dict = {}
    any_term = False

    def sentence_asserts(sent: str, terms: list) -> tuple:
        """(hit_state, start, end): first non-negated term occurrence."""
        for term in terms:
            start = sent.find(term)
            if start < 0:
                continue
            if term_negated(sent, start, start + len(term), lang) == "asserted":
                return ("asserted", start, start + len(term))
            return ("negated", start, start + len(term))
        return ("absent", -1, -1)

    GENERIC_MENISCUS = ["menisc", "menisk", "μηνισκ", "мениск"]
    MENISCUS_BY_COMPARTMENT = {
        "Medial Meniscus": MEDIAL_WORDS,
        "Lateral Meniscus": LATERAL_WORDS,
    }

    COMPARTMENT_OA = {
        "Medial OA": MEDIAL_WORDS,
        "Lateral OA": LATERAL_WORDS,
        "PF OA": PF_WORDS,
    }

    for finding, terms in LEXICON.items():
        found = []
        for sent in norm_sentences:
            if finding in CONJUNCTIONS:
                # structure term + non-negated tear word in the same sentence
                state, _, _ = sentence_asserts(sent, terms)
                if (
                    state == "absent"
                    and finding in MENISCUS_BY_COMPARTMENT
                    # laterality carried by the compartment word: generic
                    # meniscus noun + this finding's side word in the sentence
                    and any(g in sent for g in GENERIC_MENISCUS)
                    and any(w in sent for w in MENISCUS_BY_COMPARTMENT[finding])
                ):
                    state = sentence_asserts(sent, GENERIC_MENISCUS)[0]
                if state == "absent":
                    continue
                any_term = True
                tstate, _, _ = sentence_asserts(sent, TEAR_WORDS)
                if state == "asserted" and tstate == "asserted":
                    found.append(sent[:120])
                    break
            elif finding in COMPARTMENT_OA:
                # compartment word + non-negated degeneration word
                if not any(w in sent for w in COMPARTMENT_OA[finding]):
                    continue
                dstate, _, _ = sentence_asserts(sent, DEGEN_WORDS)
                if dstate != "absent":
                    any_term = True
                if dstate == "asserted":
                    found.append(sent[:120])
                    break
            else:
                state, _, _ = sentence_asserts(sent, terms)
                if state == "absent":
                    continue
                any_term = True
                if (
                    state == "asserted"
                    and finding == "Effusion"
                    and any(q in sent for q in SMALLNESS_WORDS)
                ):
                    state = "negated"  # gold excludes trace/minimal effusions
                if (
                    state == "asserted"
                    and finding == "Contusion"
                    and any(q in sent for q in REACTIVE_EDEMA_CONTEXT)
                ):
                    state = "negated"  # reactive/subchondral edema is not a bruise
                if state == "asserted":
                    found.append(sent[:120])
                    break
        labels[finding] = 1 if found else 0
        if found:
            hits[finding] = found
    return {
        "labels": labels,
        "language": lang,
        "hits": hits,
        "coverage": "terms_found" if any_term else "no_terms_found",
    }
