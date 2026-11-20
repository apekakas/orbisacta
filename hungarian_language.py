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
    # "waste crime" mistranslated into a non-existent Hungarian word.
    (r"\bhulladékrémállyal\b", "illegális hulladékkezeléssel"),
    (r"\bhulladékrémály\w*", "illegális hulladékkezelés"),
    (r"\bBelgaország", "Belgium"),
)

# Do not touch years, date notation (2024.11.20), thousands-grouped numbers,
# versions, URLs or strings containing other dots.
DECIMAL = re.compile(r"(?<![\d.])(\d{1,3})\.(\d{1,2})(?![\d.])")

# English thousands grouping in unambiguous monetary amounts, e.g.
# "10,000 font", "71,000 font". Do not rewrite bare 0,125 values
# or decimals where no supported currency noun follows.
CURRENCY_THOUSANDS = re.compile(
    r"(?<![\d.,])([1-9]\d{0,2}),([0-9]{3})(?=\s*(?:font(?:ot|tal|ban|ból|nak)?|"
    r"euró(?:t|val|ban|ból)?|dollár(?:t|ral|ban|ból)?|forint(?:ot|tal|ban|ból)?)\b)",
    re.IGNORECASE,
)

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
    text = CURRENCY_THOUSANDS.sub(r"\1 \2", text)
    return DECIMAL.sub(r"\1,\2", text)


def check_hungarian_language(text):
    """Flag clearly untranslated phrases, not speculative stylistic issues."""
    if not isinstance(text, str) or not text.strip():
        return False, "empty_hungarian_text"
    if re.search(r"\bhulladékrémál\w*", text, flags=re.IGNORECASE):
        return False, "nonsensical_waste_crime_translation"
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


# Editorially verified, stable acronym expansions. These are word meanings,
# not new assertions about the event reported in a source article. Do NOT
# auto-expand ambiguous or unfamiliar acronyms from guessed meanings.
VERIFIED_ABBREVIATIONS = {
    "STEM": "természettudományok, technológia, mérnöki tudományok és matematika",
    "GDP": "bruttó hazai termék",
    "WHO": "Egészségügyi Világszervezet",
    "OECD": "Gazdasági Együttműködési és Fejlesztési Szervezet",
}
UNEXPLAINED_ABBREVIATION_EXCEPTIONS = {
    "EU", "USA", "ENSZ", "NATO", "AI", "MI", "GDP", "WHO", "OECD", "STEM",
    "USD", "EUR", "HUF", "UK", "BBC", "CNN", "NASA", "API", "RSS",
}


def expand_verified_abbreviations(text):
    """Explain known acronyms ONCE per summary, never change quantitative data.

    Avoid double expansions where the abbreviation is already explicitly
    defined in the immediately following parenthesis. Other abbreviations
    are left untouched instead of hallucinating a definition.
    """
    if not isinstance(text, str):
        return text
    for acronym, definition in VERIFIED_ABBREVIATIONS.items():
        match = re.search(r"\b" + re.escape(acronym) + r"\b", text)
        if not match:
            continue
        # A source/AI may already have explained the acronym. In that case
        # do not duplicate any parenthetical definition.
        tail = text[match.end():match.end()+180]
        if re.match(r"\s*\(", tail) or definition.casefold() in text.casefold():
            continue
        # Treat a hyphenated Hungarian descriptive compound as an attribute
        # of the abbreviation rather than hanging the suffix on parentheses.
        suffix = re.match(r"-(terület\w*|hallgat\w*|szak\w*|képzés\w*)\b", tail)
        if suffix and acronym == "STEM":
            new = f"{acronym} ({definition}) {suffix.group(1)}"
            text = text[:match.start()] + new + text[match.end()+len(suffix.group(0)):]
        else:
            new = f"{acronym} ({definition})"
            text = text[:match.start()] + new + text[match.end():]
    return text


def abbreviations_for_editorial_review(text):
    """Detect potentially obscure, unexplained all-cap acronyms for review."""
    if not isinstance(text, str):
        return []
    found = set()
    for match in re.finditer(r"(?<![\w])([A-ZÁÉÍÓÖŐÚÜŰ]{2,8})(?![\w])", text):
        word = match.group(1)
        if word in UNEXPLAINED_ABBREVIATION_EXCEPTIONS:
            continue
        tail = text[match.end():match.end()+90]
        if re.match(r"\s*\(", tail):
            continue
        found.add(word)
    return sorted(found)
