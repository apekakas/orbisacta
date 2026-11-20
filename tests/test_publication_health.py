"""Offline regression tests for deployment checks."""
from datetime import datetime, timezone
import pytest
from publication_health import verify_publication


AT = datetime(2026, 11, 20, 18, tzinfo=timezone.utc)


def fixture_payload():
    status = {
        "project": "OrbisActa", "updated_utc": "2026-11-20T17:59:00+00:00",
        "feed_count": 29, "feeds_ok": 19,
        "live_article_count": 1, "items_published_in_run": 1,
        "ai_configured": True, "daily_target": 100, "published_today": 1,
    }
    news = {"project": "OrbisActa", "count": 1, "articles": [{"id": "a"}]}
    quality = {"total": {"published": 1}}
    return status, news, quality


def test_valid_payload():
    result = verify_publication(*fixture_payload(), at=AT)
    assert result["feeds_working"] == 19
    assert result["published_in_archive"] == 1


def test_stale_deployment_fails():
    s, n, q = fixture_payload()
    s["updated_utc"] = "2026-11-20T10:00:00+00:00"
    with pytest.raises(ValueError, match="stale"):
        verify_publication(s, n, q, at=AT)


def test_mismatched_counts_fail():
    s, n, q = fixture_payload()
    n["count"] = 3
    with pytest.raises(ValueError, match="article count"):
        verify_publication(s, n, q, at=AT)


def test_zero_news_is_visible_warning_not_false_success_claim():
    s, n, q = fixture_payload()
    s["live_article_count"] = 0
    n["articles"] = []
    n["count"] = 0
    q["total"]["published"] = 0
    assert "No published articles" in verify_publication(s, n, q, at=AT)["warning"]


def test_missing_api_flag_fails():
    s, n, q = fixture_payload()
    del s["ai_configured"]
    with pytest.raises(ValueError, match="AI status"):
        verify_publication(s, n, q, at=AT)


def test_feed_count_invalid_fails():
    s, n, q = fixture_payload()
    s["feeds_ok"] = 30
    with pytest.raises(ValueError, match="feed"):
        verify_publication(s, n, q, at=AT)
