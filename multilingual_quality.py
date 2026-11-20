"""Evidence-conservative cross-language translation QA.

New translations are checked for number preservation by sentence. Historical
translations are audited read-only; they are not edited or silently deleted.
No online services, language-model requests, or external dictionaries.
"""
import re
from collections import Counter
from editorial_quality import numeric_values

# Unambiguously Hungarian phrases (not international proper names) should not
# appear in non-Hungarian machine-translated news summaries.
HUNGARIAN_LEAK = re.compile(
    r"\b(?:hulladékrémál\w*|őrizetbe vétel|"
    r"pénzbírságot|"
    r"százalékponttal|"
    r"súlyos anyagi és társadalmi nélkülözés)\b",
    flags=re.IGNORECASE,
)

# Exact known pseudo-words/non-language from published feedback, not a
# speculative blanket spelling checker.
KNOWN_GARBAGE = re.compile(r"\bhulladékrémál\w*", flags=re.IGNORECASE)


def split_five(text):
    if not isinstance(text, str):
        return []
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]


def factual_numbers(text):
    """Value-normalized figures; years are checked independently."""
    return numeric_values(text)


def years_in(text):
    return set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", text or ""))


def translation_issue(lang, original, target):
    """Return a coarse non-sensitive reason or None, not translated content."""
    if lang not in {"en", "fr", "de", "es", "pt"}:
        return "unsupported_language"
    if not isinstance(target, str) or not target.strip():
        return "missing_text"
    if KNOWN_GARBAGE.search(target) or HUNGARIAN_LEAK.search(target):
        return "mixed_or_garbled_language"
    # Don't assume either language expresses figures in the same locale format.
    if factual_numbers(original) != factual_numbers(target):
        return "numeric_mismatch"
    if years_in(original) != years_in(target):
        return "year_mismatch"
    return None


def check_translation_pair(lang, original_summary, translated_sentences):
    """Check 1-to-1 correspondence: 5 facts, 5 translated sentences."""
    originals = split_five(original_summary)
    if len(originals) != 5 or len(translated_sentences) != 5:
        return "missing_parallel_sentences"
    for source, dest in zip(originals, translated_sentences):
        issue = translation_issue(lang, source, dest)
        if issue:
            return issue
    return None


def audit_translation_rows(con):
    """Aggregate historical defects with zero writes; do not publish raw text."""
    rows = con.execute(
        """SELECT a.summary_hu, t.lang, t.summary
             FROM article_translations t
             JOIN articles a ON a.id=t.article_id
            WHERE a.status='published'"""
    ).fetchall()
    audit = {lang: Counter() for lang in ("en", "es", "fr", "de", "pt")}
    for row in rows:
        lang = row["lang"]
        if lang not in audit:
            continue
        audit[lang]["checked"] += 1
        issue = check_translation_pair(lang, row["summary_hu"], split_five(row["summary"]))
        if issue:
            audit[lang][issue] += 1
    return {lang: dict(counts) for lang, counts in audit.items()}
