"""Read-only aggregate of current RSS entries vs the known article database.

Counts are feed appearances, not unique worldwide stories. No URLs, titles or
article bodies leave the job. No AI/API requests are made.
"""
from collections import Counter
from datetime import datetime, timezone, timedelta


def feed_overlap(con, entries, *, at=None, days=7):
    from orbisacta import canonical_url
    now = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = now - timedelta(days=days)
    counts = Counter()
    for item in entries:
        try:
            date = datetime.fromisoformat(str(item.get("published_utc") or "").replace("Z", "+00:00"))
            recent = date.tzinfo is not None and cutoff <= date.astimezone(timezone.utc) <= now + timedelta(minutes=5)
        except (ValueError, TypeError, OverflowError):
            recent = False
        if not recent:
            continue
        url = canonical_url(item.get("url", ""))
        if not url:
            counts["recent_invalid_url"] += 1
            continue
        row = con.execute("SELECT status FROM articles WHERE url=?", (url,)).fetchone()
        if row is None:
            counts["recent_unseen_url"] += 1
        else:
            counts["recent_known_url"] += 1
            status = row["status"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
            group = status if status in {
                "published", "pending_ai", "needs_review", "wrong_country",
                "awaiting_rights"
            } else "other"
            counts["recent_known_" + group] += 1
    return dict(counts)


def aggregate_overlap(stats):
    keys = ("recent_unseen_url", "recent_known_url", "recent_invalid_url",
            "recent_known_published", "recent_known_pending_ai",
            "recent_known_needs_review", "recent_known_wrong_country",
            "recent_known_awaiting_rights", "recent_known_other")
    return {key: sum(int(s.get(key, 0)) for s in stats) for key in keys}
