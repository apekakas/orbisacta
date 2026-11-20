"""RSS freshness diagnostics without publishing article content.

All dates must be explicit and timezone-aware; never use ingestion time as a
made-up publication date.  Aggregated counts make stale/empty feeds visible.
"""
from datetime import datetime, timedelta, timezone


def classify_dates(entries, at=None, days=7):
    now = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = now - timedelta(days=days)
    counts = {"entries_recent": 0, "entries_stale": 0,
              "entries_undated": 0, "entries_future": 0}
    for entry in entries:
        raw = entry.get("published_utc") or ""
        if not raw:
            counts["entries_undated"] += 1
            continue
        try:
            stamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (TypeError, ValueError, OverflowError):
            counts["entries_undated"] += 1
            continue
        if stamp.tzinfo is None:
            counts["entries_undated"] += 1
        elif stamp.astimezone(timezone.utc) > now + timedelta(minutes=5):
            counts["entries_future"] += 1
        elif stamp.astimezone(timezone.utc) >= cutoff:
            counts["entries_recent"] += 1
        else:
            counts["entries_stale"] += 1
    return counts


def aggregate_freshness(stats):
    return {
        "feeds_with_recent_entries": sum(x.get("entries_recent", 0) > 0 for x in stats),
        "feeds_without_recent_entries": sum(x.get("entries_recent", 0) == 0
                                            and x.get("status") == "ok" for x in stats),
        "recent_entries": sum(x.get("entries_recent", 0) for x in stats),
        "stale_entries": sum(x.get("entries_stale", 0) for x in stats),
        "undated_entries": sum(x.get("entries_undated", 0) for x in stats),
        "future_dated_entries": sum(x.get("entries_future", 0) for x in stats),
        "recovered_publication_dates": sum(x.get("dates_recovered", 0) for x in stats),
    }
