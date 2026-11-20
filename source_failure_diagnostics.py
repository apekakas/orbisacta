"""Read-only, aggregate-only editorial failure diagnostics by news source.

The CI log intentionally contains no article URLs, titles, scraped text,
model output, personal identifiers, or API credentials. Report source cohorts
to identify which HTML formats deserve source-specific extractor work.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta


def classify_review_error(message):
    reason = (message or "").lower()
    if "insufficient_article_text" in reason:
        return "short_text"
    if "evidence_not_in_article" in reason:
        return "quote_mismatch"
    if "two_evidenced_numeric_facts_required" in reason:
        return "numeric_evidence"
    if "short_evidence" in reason:
        return "short_quote"
    if "author_missing" in reason:
        return "author_missing"
    if "meta_description_without_news" in reason:
        return "meta_description"
    return "other_review"


def source_failure_breakdown(con, *, at=None, days=7):
    """Count *unique stored articles*, split by source, reason, recency, retries.

    Never fetch external pages, requeue content, call a model, or alter state.
    """
    now = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = now - timedelta(days=days)
    rows = con.execute(
        """SELECT source_id, source_name, country, status, error,
                  published_utc, extraction_retry_count
             FROM articles
            WHERE status IN ('needs_review', 'wrong_country')"""
    ).fetchall()
    by_source = defaultdict(Counter)
    for row in rows:
        published = row["published_utc"]
        try:
            parsed = datetime.fromisoformat(str(published or "").replace("Z", "+00:00"))
            fresh = (parsed.tzinfo is not None and
                     cutoff <= parsed.astimezone(timezone.utc) <= now + timedelta(minutes=5))
        except (TypeError, ValueError, OverflowError):
            fresh = False
        group = (row["source_id"], row["source_name"], row["country"])
        category = ("wrong_country" if row["status"] == "wrong_country"
                    else classify_review_error(row["error"]))
        by_source[group][category] += 1
        if fresh:
            by_source[group]["recent_" + category] += 1
        if category == "short_text" and int(row["extraction_retry_count"] or 0) > 0:
            by_source[group]["short_text_retried"] += 1
    results = []
    for (sid, name, country), counts in by_source.items():
        results.append({"source_id": sid, "source": name, "country": country,
                        **{key: counts[key] for key in (
                            "short_text", "short_text_retried", "recent_short_text",
                            "quote_mismatch", "recent_quote_mismatch",
                            "numeric_evidence", "short_quote", "author_missing",
                            "meta_description", "wrong_country",
                            "recent_wrong_country", "other_review")}})
    return sorted(results, key=lambda d: (
        -(d["short_text"] + d["quote_mismatch"] + d["numeric_evidence"]),
        d["source_id"]
    ))


def aggregate_failures(rows):
    keys = ("short_text", "short_text_retried", "recent_short_text",
            "quote_mismatch", "recent_quote_mismatch", "numeric_evidence",
            "short_quote", "author_missing", "meta_description",
            "wrong_country", "recent_wrong_country", "other_review")
    return {key: sum(row.get(key, 0) for row in rows) for key in keys}
