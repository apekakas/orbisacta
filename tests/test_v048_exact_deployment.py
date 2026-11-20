"""A deployed site must match this exact build, not an earlier cache hit."""
from datetime import datetime, timezone

import pytest

from publication_health import verify_publication


def sample():
    status = {
        "project": "OrbisActa",
        "updated_utc": "2026-11-20T22:04:00+00:00",
        "feed_count": 31,
        "feeds_ok": 30,
        "items_published_in_run": 0,
        "ai_configured": True,
        "live_article_count": 1,
    }
    news = {"project": "OrbisActa", "count": 1, "articles": [{}]}
    quality = {"total": {"published": 1}}
    return status, news, quality


def test_exact_version_match_passes():
    verify_publication(
        *sample(), at=datetime(2026, 11, 20, 22, 5, tzinfo=timezone.utc),
        expected_updated="2026-11-20T22:04:00Z"
    )


def test_still_recent_previous_version_fails():
    with pytest.raises(ValueError, match="deployed version does not match"):
        verify_publication(
            *sample(), at=datetime(2026, 11, 20, 22, 5, tzinfo=timezone.utc),
            expected_updated="2026-11-20T22:05:00+00:00"
        )


def test_workflow_passes_job_version_to_remote_check():
    from pathlib import Path
    workflow = (Path(__file__).resolve().parents[1] /
                ".github/workflows/orbisacta-online.yml").read_text(encoding="utf-8")
    assert "steps.capture_version.outputs.expected_updated" in workflow
    assert "needs.news.outputs.expected_updated" in workflow
    assert "--expected-updated" in workflow
