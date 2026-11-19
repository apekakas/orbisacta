"""Aggregate editorial coverage metrics for publicly approved news.

Only articles already eligible for public publication are examined. Metrics
are heuristic coverage indicators, not factual accuracy certifications and
not visitor popularity statistics. No extra model calls, cookies or IP data.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json

from editorial_quality import numeric_values


def source_date(value):
    """Return publication date in UTC or None for invalid/missing timestamps."""
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return stamp.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def publishable_metrics(articles, country_names, topics, archive, generated_utc,
                        publisher_lookup=None):
    """Build seven-day, per-country/per-topic indicators from public article rows.

    The numeric test detects two different statistical values in the Hungarian
    summary, excluding stand-alone years; it does NOT recheck source evidence
    for historical articles (quotes were intentionally never retained).
    Context means a source-gated explanatory block is stored, not that every
    country-specific term has been explained.
    """
    start = archive["start_date"]
    end = archive["end_date"]
    eligible = [
        row for row in articles
        if (date := source_date(row.get("published_utc"))) is not None
        and start <= date <= end
    ]
    enriched = []
    publisher_lookup = publisher_lookup or {}
    for row in eligible:
        numbers = numeric_values(row.get("summary_hu") or "", require_unit=True)
        enriched.append({
            "country": row.get("country") or "WORLD",
            "topic": row.get("topic") or "egyéb",
            "publisher": publisher_lookup.get(
                (row.get("source_name") or "").strip(),
                (row.get("source_name") or "").strip()
            ),
            "two_numeric_facts": len(numbers) >= 2,
            "has_explainer": bool((row.get("context_text") or "").strip()),
            "source_date": source_date(row.get("published_utc")),
        })

    def summarize(rows):
        publishers = Counter(row["publisher"] for row in rows if row["publisher"])
        topics_count = Counter(row["topic"] for row in rows)
        count = len(rows)
        return {
            "published": count,
            "two_numeric_facts": sum(row["two_numeric_facts"] for row in rows),
            "with_explainer": sum(row["has_explainer"] for row in rows),
            "distinct_publishers": len(publishers),
            "largest_publisher_share_pct": (
                round(100 * max(publishers.values()) / count) if count and publishers else None
            ),
            "topics": {topic: topics_count.get(topic, 0) for topic in topics},
            "most_recent_source_date": max((row["source_date"] for row in rows), default=None),
        }

    by_country = {}
    for country, name in country_names.items():
        country_rows = [row for row in enriched if row["country"] == country]
        by_country[country] = {"name_hu": name, **summarize(country_rows)}

    by_topic = {}
    for topic in topics:
        topic_rows = [row for row in enriched if row["topic"] == topic]
        by_topic[topic] = summarize(topic_rows)

    return {
        "project": "OrbisActa",
        "updated_utc": generated_utc,
        "archive": archive,
        "measurement": {
            "basis": "published_Hungarian_source_dated_news_only",
            "two_numeric_facts": "two distinct numeric statistical values detected in summary text; NOT independently reverified against original source",
            "with_explainer": "nonempty source-gated explanatory field",
            "distinct_publishers": "distinct editorial publishers after unifying their RSS feeds; not number of RSS feeds",
            "not_included": ["visitor_popularity", "personal_data", "unpublished_stories", "AI_review_errors"],
        },
        "total": summarize(enriched),
        "countries": by_country,
        "topics": by_topic,
    }


def export_quality_report(articles, country_names, topics, archive, generated_utc,
                          destination: Path, publisher_lookup=None):
    report = publishable_metrics(
        articles, country_names, topics, archive, generated_utc, publisher_lookup)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
