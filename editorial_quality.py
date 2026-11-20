"""Conservative numerical evidence and local-context safeguards.

No added model calls. The AI's factual points already contain an exact quote
from the original story; numbers must be present in both quote and summary.
"""
import re
import unicodedata
from decimal import Decimal, InvalidOperation

# Cyrillic, Han and kana characters can be directly adjacent to a number:
# e.g. 失業率4.6％ or безработица4,6%. Keep ASCII word parts excluded.
NUMBER = re.compile(r"(?<![0-9A-Za-z])(?:\d{1,3}(?:[,\.\u00a0\u202f ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?![0-9A-Za-z])")
STATISTIC_UNITS = re.compile(
    r"%|€|\$|£|\b(?:percent|per cent|million|billion|thousand|"
    r"unemployment|employment|employee|employees|workers|jobs|wages?|"
    r"average|median|growth|rate|population|residents|people|"
    r"households|salary|salaries|income|revenue|gdp|inflation|"
    r"eur|usd|gbp|kilomet(?:er|re)s?|tonnes?|tons?|"
    r"százalék\w*|millió\w*|milliárd\w*|ezer\w*|fő|foglalkoztat\w*|munkanélkül\w*|"
    r"bér\w*|lakos\w*|jövedelem\w*|árbevétel\w*|növekedés\w*|"
    r"процент\w*|миллион\w*|миллиард\w*|тысяч\w*|рубл\w*|"
    r"безработиц\w*|занятос\w*|населени\w*|доход\w*|зарплат\w*)\b|"
    r"(?:人口|失業|就業|就业|増加|增长|経済|经济|万人|万|億|亿|兆|円|元|人|件|吨|吨|％)",
    re.IGNORECASE,
)
DATE = re.compile(r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b")
YEAR = re.compile(r"^(?:19|20)\d{2}$")


def canonical_number(raw):
    """Normalize e.g. '1,234.5', '1 234,5', '12,5' for factual matching."""
    raw = raw.replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if not raw:
        return None
    if YEAR.fullmatch(raw):
        return None
    if "." in raw and "," in raw:
        decimal_sep = "." if raw.rfind(".") > raw.rfind(",") else ","
        thousands_sep = "," if decimal_sep == "." else "."
        raw = raw.replace(thousands_sep, "").replace(decimal_sep, ".")
    elif raw.count(",") > 1 or raw.count(".") > 1:
        raw = raw.replace(",", "").replace(".", "")
    elif "," in raw or "." in raw:
        sep = "," if "," in raw else "."
        a, b = raw.split(sep, 1)
        # 1,250 or 1.250 commonly denotes thousands, but 0.250 is decimal.
        raw = a + b if len(b) == 3 and a != "0" and len(a) <= 3 else a + "." + b
    try:
        return str(Decimal(raw).normalize())
    except InvalidOperation:
        return None


def numeric_values(text, require_unit=False):
    """Return numerical values, ignoring years and ISO dates.

    For triggering the two-fact editorial rule, only statistics with nearby
    units or statistical context count. For verifying a quote-to-summary link,
    any number can match; the context is supplied by the evidence quote.
    """
    cleaned = DATE.sub(" ", unicodedata.normalize("NFKC", text or ""))
    values = set()
    for hit in NUMBER.finditer(cleaned):
        val = canonical_number(hit.group())
        if val is None:
            continue
        if require_unit:
            neighborhood = cleaned[max(0, hit.start()-36):min(len(cleaned), hit.end()+36)]
            if not STATISTIC_UNITS.search(neighborhood):
                continue
        values.add(val)
    return values


def check_numeric_facts(source_text, points):
    """Require two distinct, evidenced statistics when source offers them.

    The summary's numbers alone are insufficient: the corresponding source
    quote must also contain each amount. Years and bare dates do not count.
    """
    source_values = numeric_values(source_text, require_unit=True)
    if len(source_values) < 2:
        return True, "not_a_multi_statistic_article"
    evidenced = set()
    for item in points:
        if not isinstance(item, dict):
            continue
        summary_numbers = numeric_values(str(item.get("sentence_hu", "")))
        quote_numbers = numeric_values(str(item.get("support_quote", "")))
        evidenced |= summary_numbers & quote_numbers & source_values
    if len(evidenced) < 2:
        return False, "two_evidenced_numeric_facts_required"
    return True, "ok"



# Reject vague text about the existence of an article instead of the news itself.
# Attributions such as "A jelentés szerint..." remain acceptable.
META_REPORTING = re.compile(
    r"^\s*(?:a|az|egy)\s+(?:cikk|hír|írás|tanulmány|jelentés|"
    r"beszámoló|közlemény|publikáció)\s+"
    r"(?:bemutatja|ismerteti|részletezi|áttekinti|összefoglalja|"
    r"ismertet|foglalkozik|vizsgálja)\b",
    re.IGNORECASE,
)


def check_editorial_points(points):
    """Prefer concrete reported developments over self-referential filler."""
    if not isinstance(points, list) or len(points) != 5:
        return False, "five_editorial_points_required"
    for index, point in enumerate(points, 1):
        if not isinstance(point, dict):
            return False, f"point_{index}_is_not_an_object"
        statement = str(point.get("sentence_hu", "")).strip()
        if META_REPORTING.match(statement):
            return False, f"point_{index}_meta_description_without_news"
    return True, "ok"

def validated_background(source_text, terms):
    """Return at most two one-sentence explanations of unfamiliar terms.

    Covers country-specific, scientific or economic terminology only when
    an exact original-text quotation supports the definition. Omit any
    unexplained terms instead of making up outside context.
    The supporting quotation is never exposed publicly.
    """
    if not isinstance(terms, list):
        return ""
    source = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", source_text or "")).lower()
    sentences, seen = [], set()
    for entry in terms[:6]:
        if len(sentences) == 2:
            break
        if not isinstance(entry, dict):
            continue
        term = str(entry.get("term_original", "")).strip()
        quote = str(entry.get("support_quote", "")).strip()
        explanation = str(entry.get("explanation_hu", "")).strip()
        quote_normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", quote)).lower()
        term_normalized = unicodedata.normalize("NFKC", term).lower()
        if not (2 <= len(term) <= 120 and 15 <= len(quote) <= 1200
                and 35 <= len(explanation) <= 450
                and explanation.endswith((".", "!", "?"))
                and "<" not in explanation and ">" not in explanation):
            continue
        if term_normalized not in source or quote_normalized not in source:
            continue
        if term_normalized not in quote_normalized or term_normalized in seen:
            continue
        if len(re.split(r"(?<=[.!?])\s+", explanation)) != 1:
            continue
        seen.add(term_normalized)
        sentences.append(explanation)
    return " ".join(sentences)
