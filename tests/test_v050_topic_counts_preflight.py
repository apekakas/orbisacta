"""Topic-count parity across locales and read-only pre-AI error counters."""
from datetime import datetime, timezone
from pathlib import Path

import orbisacta as oa


def test_all_six_locales_show_topic_totals_for_selected_countries_and_date():
    docs = Path(__file__).resolve().parents[1] / "docs"
    for language in ("hu", "en", "fr", "de", "es", "pt"):
        page = docs / ("index.html" if language == "hu" else language + "/index.html")
        text = page.read_text(encoding="utf-8")
        assert "const topicPool=articles.filter(a=>selected.has(a.country)&&inSelectedDate(a));" in text
        assert "const total=code==='Összes'?topicPool.length:topicPool.filter(a=>a.topic===code).length;" in text
        assert "tr('topics')[code])+' ('+total+')'" in text
        assert "topicEl.append(btn(label,topic===code" in text


def test_preflight_errors_are_separate_from_ai_attempts(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / "preflight.sqlite")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    authors = {"id": "authors", "name": "Author-required", "country": "GB",
               "topic_hint": "egyéb", "ai_approved": True, "author_required": True}
    short = {"id": "short", "name": "Short-page", "country": "US",
             "topic_hint": "egyéb", "ai_approved": True, "author_required": False}
    oa.insert_entries(con, authors, [{
        "url": "https://example.org/authors", "title": "Article without required author",
        "published_utc": now, "author": ""
    }])
    oa.insert_entries(con, short, [{
        "url": "https://example.org/short", "title": "A short article",
        "published_utc": now, "author": "Editorial Team"
    }])
    monkeypatch.setenv("OPENAI_API_KEY", "mock-secret")
    monkeypatch.setattr(oa, "extract_article_text", lambda url: "A short excerpt.")
    def fail_if_called(*args):
        raise AssertionError("AI must never be called during failed preflight")
    monkeypatch.setattr(oa, "ai_summarize", fail_if_called)
    report = oa.process(con, [authors, short], max_items=3, model="test")
    assert report["processed"] == 0
    assert report["published"] == 0
    assert report["preflight_checked"] == 2
    assert report["preflight_errors"]["author_missing"] == 1
    assert report["preflight_errors"]["insufficient_article_text"] == 1
    assert report["preflight_errors"]["source_fetch_error"] == 0
    con.close()


def test_article_fetch_failure_is_reported_before_ai(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / "fetch.sqlite")
    src = {"id": "source", "name": "Source", "country": "GB",
           "topic_hint": "egyéb", "ai_approved": True}
    oa.insert_entries(con, src, [{
        "url": "https://example.org/story", "title": "Story",
        "published_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }])
    monkeypatch.setenv("OPENAI_API_KEY", "mock-secret")
    class HTTPError(Exception):
        pass
    def fail_fetch(url):
        raise HTTPError("Cannot fetch article")
    monkeypatch.setattr(oa, "extract_article_text", fail_fetch)
    report = oa.process(con, [src], max_items=2)
    assert report["processed"] == 0
    assert report["preflight_errors"]["source_fetch_error"] == 1
    con.close()
