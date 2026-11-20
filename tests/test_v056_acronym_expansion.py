"""v0.5.6: established abbreviations are explained on first use in Hungarian."""
import json
from datetime import datetime, timezone

import orbisacta as oa
from hungarian_language import (
    abbreviations_for_editorial_review,
    expand_verified_abbreviations,
)
from editorial_quality import numeric_values


STEM_EXAMPLE = (
    "2025-re a STEM területen végzett felsőfokú végzettséggel rendelkező emberek "
    "aránya 8,5% volt az EU 15-74 éves népességében. "
    "Írországban volt a legmagasabb a STEM területen végzett felsőfokú "
    "végzettséggel rendelkező emberek aránya, 12,0%. "
    "A legmagasabb arányú STEM hallgatók 2024-ben Írországban (36,4%) voltak. "
    "2015 és 2024 között Írországban a STEM hallgatók aránya 26,8%-ról "
    "36,4%-ra nőtt. A legnagyobb csökkenést a STEM hallgatók körében "
    "Máltán (-8,2%) regisztrálták."
)
STEM_DEFINITION = "természettudományok, technológia, mérnöki tudományok és matematika"


def test_stem_explained_once_not_every_time():
    revised = expand_verified_abbreviations(STEM_EXAMPLE)
    assert revised.count(STEM_DEFINITION) == 1
    assert "STEM (" + STEM_DEFINITION + ")" in revised
    assert revised.count("STEM") == STEM_EXAMPLE.count("STEM")
    assert numeric_values(revised) == numeric_values(STEM_EXAMPLE)
    assert expand_verified_abbreviations(revised) == revised
    assert "EU (" not in revised


def test_existing_explanation_not_duplicated():
    already = "STEM (természettudományok, technológia, mérnöki tudományok és matematika) képzésekről írtak."
    assert expand_verified_abbreviations(already) == already


def test_hyphenated_first_occurrence_remains_readable():
    revised = expand_verified_abbreviations("2025-ben a STEM-területen 8,5% volt az arány.")
    assert "STEM (" + STEM_DEFINITION + ") területen" in revised
    assert "8,5%" in revised


def test_unknown_or_ambiguous_acronyms_are_not_fabricated():
    sample = "A XZY bizottság jelentést készített; az EU részt vett."
    revised = expand_verified_abbreviations(sample)
    assert revised == sample
    assert abbreviations_for_editorial_review(sample) == ["XZY"]


def test_previous_published_stem_summary_backfilled_without_database_edits(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / "site.sqlite")
    source = {"id":"verified", "name":"Verified Source", "country":"EU",
              "ai_approved":True, "topic_hint":"tudomány"}
    oa.insert_entries(con, source, [{
        "url":"https://example.org/stem", "title":"STEM news",
        "published_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")
    }])
    con.execute("""UPDATE articles SET status='published',
                   topic='tudomány', title_hu='STEM-adatok',
                   summary_hu=?""", (STEM_EXAMPLE,))
    con.commit()
    monkeypatch.setattr(oa, "load_sources",
                        lambda *args: [dict(source, publisher="Verified Source")])
    export = tmp_path / "docs" / "news.json"
    assert oa.export_json(con, export) == 1
    article = json.loads(export.read_text(encoding="utf-8"))["articles"][0]
    assert article["summary_hu"].count(STEM_DEFINITION) == 1
    assert con.execute("SELECT summary_hu FROM articles").fetchone()[0] == STEM_EXAMPLE
    con.close()


def test_policy_for_all_new_acronyms_present():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    policy=(root/"SZERKESZTESI_ALAPELVEK.md").read_text(encoding="utf-8")
    prompt=(root/"orbisacta.py").read_text(encoding="utf-8")
    assert "rövidítéseket első előforduláskor feloldjuk" in policy
    assert "GENERAL ABBREVIATION RULE" in prompt
    assert "Do not guess ambiguous acronyms" in prompt
