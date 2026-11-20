"""Reader-first Hungarian newsroom policy regression tests."""
from pathlib import Path

import orbisacta as oa
from hungarian_language import polish_hungarian


SAMPLE = (
    "2025-ben az EU népességének 6,3%-a súlyos anyagi és társadalmi "
    "deprivációt tapasztalt. A nőknél a súlyos anyagi és társadalmi "
    "deprivációs ráta 6,6%-ot ért el, ami magasabb a férfiak 6,0%-ánál. "
    "18 és 64 év között a nők 6,7%-os, míg a férfiak 5,9%-os "
    "deprivációs rátával rendelkeztek. A 65 éven felüliek körében "
    "a legalacsonyabb, 4,9%-os deprivációs rátát regisztrálták. "
    "A férfiak 65 éves kor felett 4,1%-os deprivációs rátát mutattak, "
    "ami alacsonyabb, mint a nők 5,5%-a."
)


def test_deprivation_example_uses_plain_language_without_moving_figures():
    revised = polish_hungarian(SAMPLE)
    assert "súlyos anyagi és társadalmi nélkülözést" in revised
    assert "súlyos anyagi és társadalmi nélkülözés aránya" in revised
    assert "depriváció" not in revised
    for figure in ("6,3%", "6,6%", "6,0%", "6,7%", "5,9%",
                   "4,9%", "4,1%", "5,5%"):
        assert figure in revised
    assert revised.count("%") == SAMPLE.count("%")


def test_reader_first_policy_is_persistent_and_source_evidence_is_preserved():
    root = Path(__file__).resolve().parents[1]
    rules = (root / "SZERKESZTESI_ALAPELVEK.md").read_text(encoding="utf-8")
    pipeline = (root / "orbisacta.py").read_text(encoding="utf-8")
    assert "Közérthető hírek szerkesztési alapelve" in rules
    assert "READER-FIRST EDITORIAL PRINCIPLE" in pipeline
    assert "Do not fabricate a statistical indicator's methodology" in pipeline
    assert "The support_quote fields MUST remain exact" in pipeline


def test_plain_language_does_not_append_unsourced_definition():
    revised = polish_hungarian("A deprivációs ráta 6,3% volt.")
    assert "6,3%" in revised
    assert "13" not in revised  # a methodological threshold requires source proof
    assert "nélkülözés aránya" in revised


def test_specialist_term_in_source_quote_is_not_autocorrected():
    source = "The severe material and social deprivation rate was 6.3%."
    points = [{
        "sentence_hu": "A súlyos anyagi és társadalmi deprivációs ráta 6,3% volt.",
        "support_quote": "severe material and social deprivation rate was 6.3%"
    }]
    source_quote = points[0]["support_quote"]
    points[0]["sentence_hu"] = polish_hungarian(points[0]["sentence_hu"])
    assert source_quote == points[0]["support_quote"]
    assert "nélkülözés aránya" in points[0]["sentence_hu"]
