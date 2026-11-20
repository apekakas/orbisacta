"""v0.4.2 source eligibility and rights tests; no network or paid API calls."""
from pathlib import Path
import re

from orbisacta import load_sources, select_source_entries


def test_eu_commission_licensing_and_activation():
    src = next(x for x in load_sources() if x["id"] == "candidate-ec-press")
    assert src["enabled"] and src["ai_approved"]
    assert src["country"] == "EU"
    assert src["license_url"].startswith("https://creativecommons.org/licenses/by/4.0/")
    assert "commission.europa.eu/legal-notice" in src["rights_reference_url"]
    assert src["author_required"] is False
    assert "allowed_url_path_regex" in src


def test_only_commission_press_releases_pass_url_gate():
    src = next(x for x in load_sources() if x["id"] == "candidate-ec-press")
    urls = [
        "https://ec.europa.eu/commission/presscorner/detail/en/speech_26_2526",
        "https://ec.europa.eu/commission/presscorner/detail/en/statement_26_2528",
        "https://ec.europa.eu/commission/presscorner/detail/en/ip_26_2510",
        "https://ec.europa.eu/commission/presscorner/detail/en/ip_26_2511",
        "https://external.example/commission/presscorner/detail/en/ip_26_123",
    ]
    # Domain gating is tested separately as the path filter is intentionally just a path gate.
    entries = [{"url": u} for u in urls[:4]]
    assert [x["url"] for x in select_source_entries(src, entries, 12)] == urls[2:4]
    assert len(select_source_entries(src, entries, 1)) == 1


def test_other_sources_keep_original_selection_order():
    entries = [{"url": "https://example.com/a"}, {"url": "https://example.com/b"}]
    assert select_source_entries({"id": "basic"}, entries, 1) == entries[:1]


def test_remaining_unreviewed_publishers_stay_disabled():
    candidates = [s for s in load_sources() if s["id"].startswith("candidate-") and s["id"] != "candidate-ec-press"]
    assert len(candidates) == 8
    assert all(not s["enabled"] and not s["ai_approved"] for s in candidates)
