"""v0.4.6 licensed GOV.UK news-only source guard; offline."""
from orbisacta import load_sources, select_source_entries


def test_govuk_source_is_explicitly_licensed_and_country_labeled():
    s = next(x for x in load_sources() if x["id"] == "govuk-news")
    assert s["enabled"] is True and s["ai_approved"] is True
    assert s["country"] == "GB"
    assert s["rss_url"] == "https://www.gov.uk/search/news-and-communications.atom"
    assert "open-government-licence/version/3" in s["license_url"]
    assert s["rights_reference_url"] == "https://www.gov.uk/help/terms-conditions"


def test_govuk_news_only_filter_excludes_nonnews_and_external_hosts():
    s = next(x for x in load_sources() if x["id"] == "govuk-news")
    entries = [
        {"url": "https://www.gov.uk/government/speeches/prime-minister-speech"},
        {"url": "https://www.gov.uk/government/news/uk-energy-project"},
        {"url": "https://www.gov.uk/government/publications/government-report"},
        {"url": "https://www.gov.uk/government/news/new-technology-announcement"},
        {"url": "https://not-gov.example/government/news/claim"},
        {"url": "https://www.gov.uk/government/news/extra/path"},
    ]
    assert select_source_entries(s, entries, 12) == [entries[1], entries[3]]
    assert select_source_entries(s, entries, 1) == [entries[1]]


def test_unreviewed_media_publishers_remain_disabled():
    s = load_sources()
    c = [x for x in s if x["id"].startswith("candidate-")]
    assert len(c) == 8
    assert all(not x["enabled"] and not x["ai_approved"] for x in c)
