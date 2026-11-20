"""Multilingual QA: check data fidelity for five languages without models."""
from datetime import datetime, timezone

import orbisacta as oa
import international as il
from multilingual_quality import (
    audit_translation_rows, check_translation_pair, translation_issue, split_five
)

HU = [
    "2025-ben a felmérés 8,5%-os növekedést mutatott.",
    "A vizsgált körben 10 000 ember vett részt.",
    "A cég összesen 71 000 font bevételre tett szert.",
    "A részvételi arány 6,3% volt.",
    "2024-ben 36 őrizetbe vételt regisztráltak."
]
EN = [
    "In 2025 the survey recorded growth of 8.5%.",
    "A total of 10,000 people participated in the survey.",
    "The company earned a total revenue of 71,000 pounds.",
    "The participation rate was 6.3%.",
    "In 2024, authorities recorded 36 arrests."
]
FR = [
    "En 2025, l'enquête a enregistré une croissance de 8,5 %.",
    "Au total, 10 000 personnes ont participé à l'enquête.",
    "L'entreprise a réalisé des recettes de 71 000 livres.",
    "Le taux de participation était de 6,3 %.",
    "En 2024, les autorités ont recensé 36 arrestations."
]
DE = [
    "Im Jahr 2025 ergab die Erhebung einen Anstieg von 8,5 %.",
    "Insgesamt nahmen 10.000 Menschen an der Erhebung teil.",
    "Das Unternehmen erzielte Einnahmen von 71.000 Pfund.",
    "Die Teilnahmequote betrug 6,3 %.",
    "Im Jahr 2024 meldeten die Behörden 36 Festnahmen."
]
ES = [
    "En 2025 la encuesta registró un crecimiento del 8,5 %.",
    "En total participaron 10.000 personas en el estudio.",
    "La empresa obtuvo ingresos de 71.000 libras.",
    "La tasa de participación fue del 6,3 %.",
    "En 2024 las autoridades registraron 36 detenciones."
]
PT = [
    "Em 2025 o inquérito registou um crescimento de 8,5%.",
    "Participaram no inquérito 10 000 pessoas ao todo.",
    "A empresa obteve uma receita de 71 000 libras.",
    "A taxa de participação foi de 6,3%.",
    "Em 2024 as autoridades registaram 36 detenções."
]

VALID = {"en": EN, "fr": FR, "de": DE, "es": ES, "pt": PT}


def test_all_five_languages_preserve_numbers_and_years():
    for lang, sentences in VALID.items():
        assert check_translation_pair(lang, " ".join(HU), sentences) is None


def test_changed_amount_wrong_year_and_mixed_hungarian_detected():
    assert translation_issue("en", HU[2], "The company earned 17,000 pounds.") == "numeric_mismatch"
    assert translation_issue("de", HU[0], "Im Jahr 2024 ergab die Erhebung einen Anstieg von 8,5 %.") == "year_mismatch"
    assert translation_issue("fr", HU[4], "En 2024 le hulladékrémállyal était associé à 36 arrestations.") == "mixed_or_garbled_language"


def test_validation_rejects_changed_figures_for_all_languages():
    payload = {
        lang: {"title": f"Valid translated news headline for {lang}", "sentences": list(points)}
        for lang, points in VALID.items()
    }
    result = il.validate_translations(payload, original_summary=" ".join(HU))
    assert set(result) == set(VALID)
    payload["pt"]["sentences"][1] = "Participaram no inquérito 100 000 pessoas ao todo."
    try:
        il.validate_translations(payload, original_summary=" ".join(HU))
    except ValueError as exc:
        assert str(exc) == "translation_qa_numeric_mismatch_pt"
    else:
        assert False, "Numeric corruption must not pass validation"


def test_previous_translations_are_only_audited_not_rewritten(tmp_path):
    con = oa.connect(tmp_path / "cross_language.sqlite")
    src = {"id": "verified", "name": "Verified Source", "country": "GB",
           "ai_approved": True, "topic_hint": "egyéb"}
    oa.insert_entries(con, src, [{
        "url": "https://example.org/story",
        "title": "Original story",
        "published_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }])
    con.execute("""UPDATE articles SET status='published',
                   summary_hu=?""", (" ".join(HU),))
    aid = con.execute("SELECT id FROM articles").fetchone()[0]
    for lang, sentences in VALID.items():
        text = " ".join(sentences)
        if lang == "es":
            text = text.replace("71.000", "17.000")
        con.execute("""INSERT INTO article_translations
                       (article_id, lang, title, summary, translated_utc)
                       VALUES (?,?,?,?,?)""",
                    (aid, lang, "Translated title", text, datetime.now(timezone.utc).isoformat()))
    con.commit()
    original_count = con.execute("SELECT count(*) FROM article_translations").fetchone()[0]
    audit = audit_translation_rows(con)
    assert audit["es"] == {"checked": 1, "numeric_mismatch": 1}
    for lang in ("en", "fr", "de", "pt"):
        assert audit[lang] == {"checked": 1}
    assert con.execute("SELECT count(*) FROM article_translations").fetchone()[0] == original_count
    con.close()


def test_unknown_language_is_not_automatically_repaired():
    assert translation_issue("ru", "10 ember.", "10 человек.") == "unsupported_language"
    assert split_five("A cég 8,5%-ot jelentett. A második érték 7,0%.") == [
        "A cég 8,5%-ot jelentett.", "A második érték 7,0%."
    ]
