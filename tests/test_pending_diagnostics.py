"""No network and no paid API calls."""
import sqlite3
from datetime import datetime, timezone

from pending_diagnostics import pending_breakdown, collect_breakdown


def test_pending_breakdown_distinguishes_age_and_licensing():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE articles(source_id TEXT, author TEXT, published_utc TEXT, status TEXT)")
    con.executemany("INSERT INTO articles VALUES (?,?,?,?)", [
        ("licensed", "Editor", "2026-11-20T10:00:00+00:00", "pending_ai"),
        ("licensed", "Editor", "2026-11-01T10:00:00+00:00", "pending_ai"),
        ("licensed", "Editor", "", "pending_ai"),
        ("not-approved", "Editor", "2026-11-20T10:00:00+00:00", "pending_ai"),
        ("byline", "", "2026-11-20T10:00:00+00:00", "pending_ai"),
        ("licensed", "Editor", "2026-11-20T10:00:00+00:00", "published"),
    ])
    sources = [
        {"id": "licensed", "enabled": True, "ai_approved": True},
        {"id": "byline", "enabled": True, "ai_approved": True, "author_required": True},
        {"id": "not-approved", "enabled": True, "ai_approved": False},
    ]
    at = datetime(2026, 11, 20, 20, tzinfo=timezone.utc)
    d = pending_breakdown(con, sources, at)
    assert d["pending_total"] == 5
    assert d["recent_eligible_for_preflight"] == 1
    assert d["older_than_seven_days"] == 1
    assert d["missing_publication_date"] == 1
    assert d["not_authorized_for_ai"] == 1
    assert d["recent_author_missing"] == 1
    con.close()


def test_intake_reports_empty_feeds_separately_from_success():
    d = collect_breakdown([
        {"status": "ok", "read": 0, "new": 0},
        {"status": "ok", "read": 12, "new": 2},
        {"status": "error", "new": 0},
    ])
    assert d == {
        "feeds_checked": 3, "feeds_fetch_ok": 2,
        "feeds_empty": 1, "entries_read": 12,
        "entries_new": 2, "feed_errors": 1,
    }


def test_processing_selects_approved_sources_before_limit(monkeypatch, tmp_path):
    import orbisacta as oa
    con = oa.connect(tmp_path / "test.sqlite3")
    recent = "2026-11-20T19:00:00+00:00"
    for i in range(210):
        con.execute("""INSERT INTO articles(id, country, topic_hint, source_id, source_name,
                  author, title_original, url, published_utc, status, ingested_utc)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (f"x{i}", "WORLD", "egyéb", "unapproved", "Unapproved",
                     "", f"Placeholder {i}", f"https://example.org/{i}", recent,
                     "pending_ai", recent))
    con.execute("""INSERT INTO articles(id, country, topic_hint, source_id, source_name,
              author, title_original, url, published_utc, status, ingested_utc)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
              ("good", "WORLD", "egyéb", "approved", "Approved", "",
               "A credible source title", "https://example.org/good", recent,
               "pending_ai", recent))
    con.commit()
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setattr(oa, "extract_article_text", lambda url: "readable " * 100)
    called = []
    def fake_summarize(*args):
        called.append(args[0]["id"])
        raise ValueError("simulated_review")
    monkeypatch.setattr(oa, "ai_summarize", fake_summarize)
    # Fixed historical UTC date makes sample articles recent.
    class FrozenDateTime:
        @staticmethod
        def now(tz):
            return datetime(2026, 11, 20, 21, tzinfo=timezone.utc)
    monkeypatch.setattr(oa, "datetime", FrozenDateTime)
    result = oa.process(con, [
        {"id": "approved", "ai_approved": True, "enabled": True},
        {"id": "unapproved", "ai_approved": False, "enabled": True}
    ], max_items=1, model="fake")
    assert result["processed"] == 1
    assert called == ["good"]
    con.close()
