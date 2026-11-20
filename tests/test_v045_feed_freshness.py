"""No paid API or HTTP requests; source freshness and date repair safety."""
from datetime import datetime, timezone
import orbisacta as oa
from feed_freshness import classify_dates
from pending_diagnostics import collect_breakdown


def test_rss_dc_date_without_pubdate():
    xml = b'''<?xml version="1.0"?>
    <rss xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
      <channel><item><title>New report</title>
      <link>https://example.org/report</link>
      <dc:date>2026-11-20T11:20:00+01:00</dc:date>
      </item></channel></rss>'''
    rows = oa.parse_feed(xml)
    assert rows[0]["published_utc"] == "2026-11-20T10:20:00+00:00"


def test_atom_link_without_rel_and_updated_timestamp():
    xml = b'''<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry><title>New bulletin</title>
      <link href="https://example.org/bulletin"/>
      <updated>2026-11-20T11:20:00Z</updated></entry></feed>'''
    rows = oa.parse_feed(xml)
    assert rows[0]["url"] == "https://example.org/bulletin"
    assert rows[0]["published_utc"] == "2026-11-20T11:20:00+00:00"


def test_no_timestamp_is_invented():
    assert oa.parse_date("") == ""
    assert oa.parse_date("2026-11-20T11:00:00") == ""
    assert oa.parse_date("not a date") == ""


def test_freshness_discriminates_real_recent_and_missing_dates():
    at = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
    entries = [
        {"published_utc": "2026-11-20T11:00:00+00:00"},
        {"published_utc": "2026-11-01T11:00:00+00:00"},
        {"published_utc": ""},
        {"published_utc": "2026-11-22T11:00:00+00:00"},
    ]
    counts = classify_dates(entries, at=at)
    assert counts == {
        "entries_recent": 1, "entries_stale": 1,
        "entries_undated": 1, "entries_future": 1,
    }


def test_duplicate_source_entry_repairs_missing_date_without_reprocessing(tmp_path):
    con = oa.connect(tmp_path / "repair.sqlite")
    source = {
        "id": "test", "country": "US", "name": "Test Source",
        "ai_approved": True, "license": "gov",
        "license_url": "https://example.org/license",
        "rights_reference_url": "https://example.org/rights"
    }
    row = {
        "url": "https://example.org/story",
        "title": "A previously known item",
        "author": "Editor",
        "published_utc": "",
    }
    oa.insert_entries(con, source, [row])
    row["published_utc"] = "2026-11-20T12:00:00+00:00"
    result = oa.insert_entries(con, source, [row])
    saved = con.execute("SELECT status, published_utc FROM articles").fetchone()
    assert result["new"] == 0 and result["dates_recovered"] == 1
    assert saved["status"] == "pending_ai"
    assert saved["published_utc"] == row["published_utc"]
    con.close()


def test_aggregate_metrics_preserve_existing_intake_fields():
    result = collect_breakdown([
        {"status": "ok", "read": 5, "new": 2, "entries_recent": 3,
         "entries_stale": 2, "dates_recovered": 1},
        {"status": "ok", "read": 4, "new": 0, "entries_stale": 4},
    ])
    assert result["entries_read"] == 9
    assert result["entries_new"] == 2
    assert result["feeds_with_recent_entries"] == 1
    assert result["feeds_without_recent_entries"] == 1
    assert result["stale_entries"] == 6
    assert result["recovered_publication_dates"] == 1
