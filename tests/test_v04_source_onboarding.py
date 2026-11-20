"""v0.4 source onboarding: candidates must be staged, never silently published."""
from pathlib import Path
import json
from orbisacta import load_sources, select_diverse_pending

ROOT = Path(__file__).resolve().parents[1]


def test_source_candidates_are_disabled_until_rights_review():
    sources = load_sources(ROOT / "sources.json")
    candidates = [s for s in sources if s["id"].startswith("candidate-")]
    assert len(candidates) >= 9
    assert all(not s["enabled"] and not s["ai_approved"] for s in candidates)
    assert len({s["publisher"] for s in candidates}) >= 6
    assert len({s["country"] for s in candidates}) >= 6


def test_candidate_lookahead_respects_more_than_40_rows():
    # The selector must not have the old fixed 40-item ceiling.
    # A single row with duplicate country is enough to exercise its loop.
    class R(dict):
        def keys(self):
            return super().keys()
    rows = [R(country="HU", published_utc="2026-11-20T10:00:00+00:00",
              source_id=f"source-{i}") for i in range(75)]
    selected = select_diverse_pending(rows, 75)
    assert len(selected) == 75
