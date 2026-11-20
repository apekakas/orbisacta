"""v0.5.3 Hungarian style regressions, source evidence and number safety."""
from datetime import datetime, timezone
import json

import orbisacta as oa
from hungarian_language import polish_hungarian, check_hungarian_language
from editorial_quality import numeric_values


BAD_EXAMPLE = (
    "2024-ben az EU-ban összesen 560 730 masztektómiát végeztek "
    "a mammákat érintő rák megelőzésére vagy kezelésére. "
    "Az EU-ban 160 928 total mastectomy-t hajtottak végre, "
    "ami 70.1 masztektómiát jelent 100 000 női lakosra vetítve. "
    "Belgaország a legmagasabb arányt mutatta, "
    "138.7 masztektómiával 100 000 női lakosra. "
    "A részleges masztektómiák száma 399 802 volt, "
    "ami 174.0-el egyenlő 100 000 női lakosra vetítve 2024-ben. "
    "A legalacsonyabb arányt Lengyelország regisztrálta, "
    "26.5 részleges masztektómiával 100 000 lakosra."
)


def test_user_example_fixed_and_figures_preserved():
    revised = polish_hungarian(BAD_EXAMPLE)
    assert "emlőrák" in revised
    assert "teljes emlőeltávolítást" in revised
    assert "Belgium" in revised
    assert "70,1" in revised
    assert "138,7" in revised
    assert "174,0" in revised
    assert "26,5" in revised
    assert "560 730" in revised
    assert "160 928" in revised
    assert "399 802" in revised
    assert "total mastectomy" not in revised
    assert numeric_values(revised) == numeric_values(BAD_EXAMPLE)
    assert check_hungarian_language(revised)[0]


def test_dates_versions_and_thousand_groups_preserved():
    original = "2024.11.20. 1.250 résztvevő. A változat 2.1.0, 70.1 százalék."
    changed = polish_hungarian(original)
    assert "2024.11.20." in changed
    assert "1.250" in changed
    assert "2.1.0" in changed
    assert "70,1" in changed


def test_hungarian_style_fails_closed_for_untranslated_copy():
    assert check_hungarian_language("Az EU-ban total mastectomy-t végeztek.") == (
        False, "untranslated_foreign_term")
    assert check_hungarian_language("Belgaországban történtek az esetek.")[0] is False
    assert check_hungarian_language("Belgiumban teljes emlőeltávolítást végeztek.")[0]


def test_exact_evidence_quote_not_changed_by_polishing():
    source = "The medical report stated that total mastectomy was carried out."
    point = {"sentence_hu": "A jelentés a total mastectomy eljárást vizsgálta.",
             "support_quote": "total mastectomy was carried out"}
    original_quote = point["support_quote"]
    point["sentence_hu"] = polish_hungarian(point["sentence_hu"])
    assert point["support_quote"] == original_quote
    assert check_hungarian_language(point["sentence_hu"])[0]


def test_hungarian_export_backfills_existing_published_briefs(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / "published.sqlite")
    s = {"id": "licensed", "name": "Sample Source", "country": "GB",
         "ai_approved": True, "topic_hint": "tudomány"}
    oa.insert_entries(con, s, [{
        "url": "https://example.org/story", "title": "Original headline",
        "published_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }])
    con.execute("""UPDATE articles SET status='published', topic='tudomány',
        title_hu='Belgaország példája', summary_hu=?""", (BAD_EXAMPLE,))
    con.commit()
    # The existing export also produces other language files and quality metrics.
    monkeypatch.setattr(oa, "load_sources", lambda *args: [dict(s, publisher="Sample Source")])
    path = tmp_path / "docs" / "news.json"
    assert oa.export_json(con, path) == 1
    published = json.loads(path.read_text(encoding="utf-8"))["articles"][0]
    assert "Belgium" in published["title_hu"]
    assert "emlőrák" in published["summary_hu"]
    assert "70,1" in published["summary_hu"]
    stored = con.execute("SELECT summary_hu FROM articles").fetchone()[0]
    assert stored == BAD_EXAMPLE  # no database rewrite, no invented new facts
    con.close()
