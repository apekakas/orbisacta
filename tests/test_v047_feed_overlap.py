"""Offline tests for RSS recency/deduplication diagnostics."""
from datetime import datetime, timezone
import orbisacta as oa
from feed_overlap import feed_overlap, aggregate_overlap
from pending_diagnostics import collect_breakdown


def test_recent_feed_items_distinguish_new_from_already_reviewed(tmp_path):
    con = oa.connect(tmp_path / "overlap.sqlite")
    src = {"id": "example", "name": "Example", "country": "GB",
           "topic_hint": "politika", "ai_approved": True}
    at = datetime(2026, 11, 20, 21, tzinfo=timezone.utc)
    entries = [
        {"url": "https://example.org/published", "title": "Published",
         "published_utc": "2026-11-20T19:00:00+00:00"},
        {"url": "https://example.org/review", "title": "Needs review",
         "published_utc": "2026-11-20T18:00:00+00:00"},
        {"url": "https://example.org/new", "title": "New",
         "published_utc": "2026-11-20T18:00:00+00:00"},
        {"url": "https://example.org/old", "title": "Old",
         "published_utc": "2026-11-01T18:00:00+00:00"},
        {"url": "https://example.org/undated", "title": "Undated",
         "published_utc": ""},
    ]
    oa.insert_entries(con, src, entries[:2])
    con.execute("UPDATE articles SET status='published' WHERE url='https://example.org/published'")
    con.execute("UPDATE articles SET status='needs_review' WHERE url='https://example.org/review'")
    con.commit()
    result = feed_overlap(con, entries, at=at)
    assert result == {
        "recent_known_url": 2,
        "recent_known_published": 1,
        "recent_known_needs_review": 1,
        "recent_unseen_url": 1,
    }
    con.close()


def test_aggregate_counts_are_appearances_not_unique_sources():
    a = {"recent_known_url": 5, "recent_known_published": 3,
         "recent_known_pending_ai": 2, "recent_unseen_url": 0}
    b = {"recent_known_url": 2, "recent_known_needs_review": 2,
         "recent_unseen_url": 1}
    sums = aggregate_overlap([a, b])
    assert sums["recent_known_url"] == 7
    assert sums["recent_unseen_url"] == 1
    assert sums["recent_known_pending_ai"] == 2
    assert collect_breakdown([a, b])["recent_known_needs_review"] == 2


def test_freshness_does_not_classify_future_as_new(tmp_path):
    con = oa.connect(tmp_path / "future.sqlite")
    at = datetime(2026, 11, 20, 21, tzinfo=timezone.utc)
    rows = [
        {"url": "https://example.org/future", "published_utc": "2026-11-22T13:00:00+00:00"},
        {"url": "https://example.org/bad", "published_utc": "not-a-date"},
        {"url": "https://example.org/naive", "published_utc": "2026-11-20T12:00:00"},
    ]
    assert feed_overlap(con, rows, at=at) == {}
    con.close()
