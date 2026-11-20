"""Conservative Hungarian copy-editing for editorial summaries.

Only unambiguous glossary corrections and decimal separator typography.
Never translate source evidence, modify the original URL, or change quantities.
The editorial source-fact validation still runs on the translated statements.
"""
import re

# These are exact, context-safe corrections; not a general machine translator.
# Keep this list deliberately small and review each addition editorially.
TERMS = (
    (r"\btotal mastectom(?:y|ies)-t\b", "teljes emlőeltávolítást"),
    (r"\btotal mastectom(?:y|ies)\b", "teljes emlőeltávolítás"),
    (r"\bpartial mastectom(?:y|ies)-t\b", "részleges emlőeltávolítást"),
    (r"\bpartial mastectom(?:y|ies)\b", "részleges emlőeltávolítás"),
    # Safe established plain-Hungarian wording for a common EU indicator.
    (r"\bsúlyos anyagi és társadalmi deprivációs rátá", "súlyos anyagi és társadalmi nélkülözés arányá"),
    (r"\bsúlyos anyagi és társadalmi deprivációt\b", "súlyos anyagi és társadalmi nélkülözést"),
    (r"\bsúlyos anyagi és társadalmi depriváció\b", "súlyos anyagi és társadalmi nélkülözés"),
    (r"\bdeprivációs rátával\b", "nélkülözési aránnyal"),
    (r"\bdeprivációs rátát\b", "nélkülözési arányt"),
    (r"\bdeprivációs ráta\b", "nélkülözés aránya"),
    (r"\bdeprivációt\b", "nélkülözést"),
        (r"\bmammákat érintő rák\b", "emlőrák"),
    (r"\bBelgaország", "Belgium"),
)

# Do not touch years, date notation (2024.11.20), thousands-grouped numbers,
# versions, URLs or strings containing other dots.
DECIMAL = re.compile(r"(?<![\d.])(\d{1,3})\.(\d{1,2})(?![\d.])")

# A narrow warning list: terms unambiguously untranslated in Hungarian briefs.
# Proper names, abbreviations and established English loanwords are not banned.
UNTRANSLATED = re.compile(
    r"\b(?:total|partial)\s+mastectom(?:y|ies)\b|"
    r"\b(?:per\s+100[ ,.]?000\s+women|mammákat érintő rák|Belgaország)\w*\b",
    flags=re.IGNORECASE,
)


def polish_hungarian(text):
    """Copy-edit known defects; leave source data and meaning untouched."""
    if not isinstance(text, str):
        return text
    for pattern, replacement in TERMS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return DECIMAL.sub(r"\1,\2", text)


def check_hungarian_language(text):
    """Flag clearly untranslated phrases, not speculative stylistic issues."""
    if not isinstance(text, str) or not text.strip():
        return False, "empty_hungarian_text"
    if UNTRANSLATED.search(text):
        return False, "untranslated_foreign_term"
    return True, "ok"


# Review-only heuristic. A technical term may be legitimate, especially when
# explained in the summary itself. This is NOT a publish/reject decision.
READER_JARGON = {
    "depriváció": re.compile(r"\bdepriváci\w*", re.IGNORECASE),
    "masztektómia": re.compile(r"\bmasztektómi\w*", re.IGNORECASE),
    "incidencia": re.compile(r"\bincidenci\w*", re.IGNORECASE),
    "prevalencia": re.compile(r"\bprevalenci\w*", re.IGNORECASE),
    "kohorsz": re.compile(r"\bkohorsz\w*", re.IGNORECASE),
    "kvantilis": re.compile(r"\bkvantilis\w*", re.IGNORECASE),
    "reálkereset": re.compile(r"\breálkereset\w*", re.IGNORECASE),
    "szubvenció": re.compile(r"\bszubvenci\w*", re.IGNORECASE),
    "penetráció": re.compile(r"\bpenetráci\w*", re.IGNORECASE),
}


def jargon_review_terms(text):
    """Return known potentially confusing expressions, not proof of a mistake."""
    if not isinstance(text, str):
        return []
    return sorted(term for term, pattern in READER_JARGON.items() if pattern.search(text))
