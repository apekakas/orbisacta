"""Read-only diagnostics for pending AI backlog, by age and authorization.

Never logs article URLs, titles, content, prompts, API secrets, or personal data.
No network / AI calls.  A feed fetch with status 'ok' can still have 0 items.
"""
from datetime import datetime, timezone, timedelta
from collections import Counter


def pending_breakdown(con, sources, at=None):
    now = at or datetime.now(timezone.utc)
    cutoff = (now.astimezone(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
    approved = {s["id"]: s for s in sources
                if s.get("enabled", True) and s.get("ai_approved")}
    rows = con.execute("""SELECT source_id, author, published_utc FROM articles
                          WHERE status='pending_ai'""").fetchall()
    result = Counter()
    for row in rows:
        result["pending_total"] += 1
        source = approved.get(row["source_id"])
        stamp = row["published_utc"]
        if not stamp:
            result["missing_publication_date"] += 1
        elif stamp < cutoff:
            result["older_than_seven_days"] += 1
        elif source is None:
            result["not_authorized_for_ai"] += 1
        elif source.get("author_required") and not (row["author"] or "").strip():
            result["recent_author_missing"] += 1
        else:
            result["recent_eligible_for_preflight"] += 1
    return {
        "pending_total": result["pending_total"],
        "recent_eligible_for_preflight": result["recent_eligible_for_preflight"],
        "recent_author_missing": result["recent_author_missing"],
        "older_than_seven_days": result["older_than_seven_days"],
        "missing_publication_date": result["missing_publication_date"],
        "not_authorized_for_ai": result["not_authorized_for_ai"],
        "seven_day_cutoff_utc": cutoff,
    }


def collect_breakdown(stats):
    from feed_freshness import aggregate_freshness
    return {
        "feeds_checked": len(stats),
        "feeds_fetch_ok": sum(x.get("status") == "ok" for x in stats),
        "feeds_empty": sum(x.get("status") == "ok" and x.get("read", 0) == 0 for x in stats),
        "entries_read": sum(int(x.get("read", 0)) for x in stats),
        "entries_new": sum(int(x.get("new", 0)) for x in stats),
        "feed_errors": sum(x.get("status") == "error" for x in stats),
        **aggregate_freshness(stats),
    }
