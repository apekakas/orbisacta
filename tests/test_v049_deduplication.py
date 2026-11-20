"""Regression tests for duplicate title false positives and observability."""
import orbisacta as oa
from deduplication import is_likely_duplicate
from pending_diagnostics import collect_breakdown


def test_same_day_exact_title_different_url_is_duplicate():
    assert is_likely_duplicate("A major announcement",
                               "2026-11-20T08:00:00+00:00",
                               "A major announcement",
                               "2026-11-20T09:00:00+00:00")


def test_similar_followup_title_next_day_is_not_silenced():
    assert not is_likely_duplicate("Minister announces new energy proposal",
                                   "2026-11-20T08:00:00+00:00",
                                   "Minister announces new energy proposals",
                                   "2026-11-18T08:00:00+00:00")


def test_exact_title_new_event_later_week_is_not_silenced():
    assert not is_likely_duplicate("Daily government briefing",
                                   "2026-11-20T08:00:00+00:00",
                                   "Daily government briefing",
                                   "2026-11-15T08:00:00+00:00")


def test_missing_dates_never_suppress_different_urls():
    assert not is_likely_duplicate("A new bulletin", "",
                                   "A new bulletin", "2026-11-20T08:00:00+00:00")


def test_different_countries_and_sources_not_silenced(tmp_path):
    con = oa.connect(tmp_path / "dedup.sqlite")
    a = {"id": "source-a", "name": "A", "country": "GB",
         "topic_hint": "politika", "ai_approved": True}
    b = {"id": "source-b", "name": "B", "country": "GB",
         "topic_hint": "politika", "ai_approved": True}
    first = {"url": "https://example.org/one",
             "title": "Breaking report on new policy",
             "published_utc": "2026-11-20T07:00:00+00:00"}
    other = {"url": "https://example.org/two",
             "title": first["title"],
             "published_utc": first["published_utc"]}
    assert oa.insert_entries(con, a, [first])["new"] == 1
    assert oa.insert_entries(con, b, [other])["new"] == 1
    con.close()


def test_same_source_near_duplicate_only_when_close_and_very_similar(tmp_path):
    con = oa.connect(tmp_path / "dedup.sqlite")
    source = {"id": "source-a", "name": "A", "country": "GB",
              "topic_hint": "politika", "ai_approved": True}
    original = {"url": "https://example.org/one",
                "title": "Minister announces new energy proposal",
                "published_utc": "2026-11-20T07:00:00+00:00"}
    a = {"url": "https://example.org/duplicate",
         "title": original["title"],
         "published_utc": "2026-11-20T10:00:00+00:00"}
    next_day = {"url": "https://example.org/next-day",
                "title": original["title"],
                "published_utc": "2026-11-23T10:00:00+00:00"}
    assert oa.insert_entries(con, source, [original])["new"] == 1
    assert oa.insert_entries(con, source, [a])["near_duplicates"] == 1
    assert oa.insert_entries(con, source, [next_day])["new"] == 1
    con.close()


def test_intake_reports_duplicate_filters_separately():
    counts = collect_breakdown([
        {"status": "ok", "read": 12, "new": 1, "duplicates": 7, "near_duplicates": 4},
        {"status": "ok", "read": 10, "new": 2, "duplicates": 5, "near_duplicates": 2},
    ])
    assert counts["entries_new"] == 3
    assert counts["entries_duplicate_urls"] == 12
    assert counts["entries_near_duplicates"] == 6
