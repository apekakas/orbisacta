"""v0.5.2 diagnostics may attribute issues without exposing original stories."""
from datetime import datetime, timedelta, timezone
import sqlite3

import orbisacta as oa
from source_failure_diagnostics import (
    aggregate_failures, classify_review_error, source_failure_breakdown,
)


def test_error_categories_are_distinct():
    assert classify_review_error("ValueError: insufficient_article_text (<550 chars)") == "short_text"
    assert classify_review_error("ValueError: point_1_evidence_not_in_article") == "quote_mismatch"
    assert classify_review_error("ValueError: two_evidenced_numeric_facts_required") == "numeric_evidence"


def test_source_failure_counts_unique_articles_and_recency(tmp_path):
    con = oa.connect(tmp_path / "qa.sqlite")
    recent = datetime.now(timezone.utc).isoformat(timespec="seconds")
    old = (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(timespec="seconds")
    source_a = {"id": "sa", "name": "Example editorial A", "country": "GB",
                "ai_approved": True, "topic_hint": "politika"}
    source_b = {"id": "sb", "name": "Example editorial B", "country": "FR",
                "ai_approved": True, "topic_hint": "gazdaság"}
    records = [
        (source_a, "one", recent, "needs_review", "ValueError: insufficient_article_text", 1),
        (source_a, "two", old, "needs_review", "ValueError: insufficient_article_text", 0),
        (source_a, "three", recent, "needs_review", "ValueError: point_2_evidence_not_in_article", 0),
        (source_a, "four", recent, "wrong_country", "country mismatch", 0),
        (source_b, "five", recent, "needs_review", "ValueError: two_evidenced_numeric_facts_required", 0),
        (source_b, "six", recent, "published", "", 0),
    ]
    for src, name, when, status, error, retry in records:
        url = "https://example.org/" + name
        oa.insert_entries(con, src, [{
            "url": url, "title": name, "published_utc": when
        }])
        con.execute("""UPDATE articles SET status=?, error=?,
                       extraction_retry_count=? WHERE url=?""",
                    (status, error, retry, url))
    con.commit()
    report = source_failure_breakdown(con)
    assert len(report) == 2
    by_id = {r["source_id"]: r for r in report}
    assert by_id["sa"]["short_text"] == 2
    assert by_id["sa"]["short_text_retried"] == 1
    assert by_id["sa"]["recent_short_text"] == 1
    assert by_id["sa"]["quote_mismatch"] == 1
    assert by_id["sa"]["recent_quote_mismatch"] == 1
    assert by_id["sa"]["wrong_country"] == 1
    assert by_id["sb"]["numeric_evidence"] == 1
    total = aggregate_failures(report)
    assert total["short_text"] == 2
    assert total["quote_mismatch"] == 1
    assert total["numeric_evidence"] == 1
    assert total["wrong_country"] == 1
    # Never expose individual stories (URL/title) through the report.
    printable = repr(report)
    assert "https://" not in printable
    assert "'one'" not in printable
    assert "'five'" not in printable
    con.close()


def test_empty_database_and_undated_entries(tmp_path):
    con = oa.connect(tmp_path / "qa_empty.sqlite")
    assert source_failure_breakdown(con) == []
    src = {"id": "s", "name": "Anonymous source", "country": "GB",
           "ai_approved": True}
    oa.insert_entries(con, src, [{
        "url": "https://example.org/undated", "title": "Unreported",
        "published_utc": ""
    }])
    con.execute("""UPDATE articles SET status='needs_review',
                   error='ValueError: insufficient_article_text'""")
    con.commit()
    report = source_failure_breakdown(con)
    assert report[0]["short_text"] == 1
    assert report[0]["recent_short_text"] == 0
    con.close()
