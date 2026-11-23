"""v0.6.0: production intake must not truncate active source RSS to 12.

The AI budget (40/run), model permissions, evidence rules, seven-day
freshness and editorial publication controls remain unchanged.
"""
from pathlib import Path
import orbisacta as oa


def test_active_feed_can_expose_30_entries_without_changing_other_rules():
    src = {"id": "govuk-news", "country": "GB", "name": "Original public source"}
    entries = [{"url": f"https://www.gov.uk/government/news/story-{i}",
                "title": f"Current original news story {i}"} for i in range(35)]
    assert len(oa.select_source_entries(src, entries, 12)) == 12
    assert len(oa.select_source_entries(src, entries, 30)) == 30
    assert oa.select_source_entries(src, entries, 30)[-1]["title"].endswith("29")


def test_production_workflow_expands_intake_without_expanding_model_budget():
    root=Path(__file__).resolve().parents[1]
    workflow=(root/".github"/"workflows"/"orbisacta-online.yml").read_text(encoding="utf-8")
    assert "--limit-per-feed 30" in workflow
    assert "--max-ai 40" in workflow
    assert "ORBIS_APPROVED_MAX_AI_PER_RUN: \"40\"" in workflow
    assert "--daily-target 100" in workflow
    assert "--max-translations 25" in workflow
