"""v0.5.1: source-only retrieval fallback and safe, one-time editorial retry."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import orbisacta as oa


def test_two_pass_extraction_uses_same_html_without_model_or_headline(monkeypatch):
    import requests
    import trafilatura
    calls = []
    class Response:
        content = b"<html><body>Editorial article</body></html>"
        def raise_for_status(self):
            return None
    def get(url, **kwargs):
        assert url == "https://example.org/report"
        calls.append(("fetch", url))
        return Response()
    def extract(blob, **kwargs):
        assert blob == Response.content
        calls.append(("extract", kwargs.get("favor_recall", False)))
        if kwargs.get("favor_recall", False):
            return "The verified report provides direct evidence. " * 28
        return "A few words only."
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(trafilatura, "extract", extract)
    result = oa.extract_article_text("https://example.org/report")
    assert len(result) >= 550
    assert calls == [("fetch", "https://example.org/report"),
                     ("extract", False), ("extract", True)]


def test_healthy_primary_extraction_does_not_run_fallback(monkeypatch):
    import requests
    import trafilatura
    class Response:
        content = b"the original article html"
        def raise_for_status(self):
            return None
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())
    calls = []
    def extract(blob, **kwargs):
        calls.append(kwargs)
        return "Verified primary reporting. " * 35
    monkeypatch.setattr(trafilatura, "extract", extract)
    assert len(oa.extract_article_text("https://example.org/news")) >= 550
    assert len(calls) == 1


def test_one_time_retry_only_for_recent_short_articles(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / "retry.sqlite")
    now = datetime.now(timezone.utc)
    src = {"id": "licensed", "name": "Licensed", "country": "GB",
           "ai_approved": True, "author_required": False}
    records = [
        ("short", "ValueError: insufficient_article_text (<550 chars)", now),
        ("evidence", "ValueError: point_1_evidence_not_in_article", now),
        ("old", "ValueError: insufficient_article_text (<550 chars)", now - timedelta(days=12)),
    ]
    for label, error, stamp in records:
        oa.insert_entries(con, src, [{
            "url": "https://example.org/" + label,
            "title": "News report " + label,
            "published_utc": stamp.isoformat(timespec="seconds")
        }])
        con.execute("UPDATE articles SET status='needs_review', error=? WHERE url=?",
                    (error, "https://example.org/" + label))
    con.commit()
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    monkeypatch.setattr(oa, "extract_article_text", lambda url: "too short")
    monkeypatch.setattr(oa, "ai_summarize", lambda *args: (_ for _ in ()).throw(
        AssertionError("Do not call AI for failed extraction")))
    first = oa.process(con, [src], max_items=4)
    assert first["extraction_retries"] == 1
    assert first["processed"] == 0
    rows = {r["url"].rsplit("/", 1)[-1]: r for r in con.execute(
        "SELECT url, status, extraction_retry_count FROM articles").fetchall()}
    assert rows["short"]["status"] == "needs_review"
    assert rows["short"]["extraction_retry_count"] == 1
    assert rows["evidence"]["extraction_retry_count"] == 0
    assert rows["old"]["extraction_retry_count"] == 0
    again = oa.process(con, [src], max_items=4)
    assert again["extraction_retries"] == 0
    assert again["processed"] == 0
    con.close()


def test_zero_capacity_does_not_change_retry_status(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / "zero.sqlite")
    src = {"id": "licensed", "name": "Licensed", "country": "GB",
           "ai_approved": True}
    oa.insert_entries(con, src, [{
        "url": "https://example.org/candidate", "title": "A short candidate",
        "published_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }])
    con.execute("""UPDATE articles SET status='needs_review',
                   error='ValueError: insufficient_article_text'""")
    con.commit()
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    report = oa.process(con, [src], max_items=0)
    assert report["reason"] == "capacity_reached"
    assert con.execute("SELECT status FROM articles").fetchone()[0] == "needs_review"
    con.close()
