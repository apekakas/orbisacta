"""OrbisActa v0.4: editorial daily target and separately authorized API budget.

The editorial target is NOT permission to spend additional API credits.
Only the operator-controlled ORBIS_APPROVED_MAX_AI_PER_RUN environment variable
can raise the conservative default API invocation ceiling of 10 per run.
"""
from datetime import datetime, timezone

DAILY_PUBLISHING_TARGET = 100
DEFAULT_APPROVED_AI_PER_RUN = 10
RUNS_PER_DAY = 4


def positive_int(value, default):
    try:
        number = int(value)
    except (ValueError, TypeError, OverflowError):
        return default
    return number if number > 0 else default


def daily_published_count(con, at=None):
    """Count new approvals by processing date (UTC), not article source date."""
    current = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    today = current.date().isoformat()
    return int(con.execute(
        "SELECT count(*) FROM articles WHERE status='published' "
        "AND processed_utc >= ? AND processed_utc < ?",
        (today + "T00:00:00", today + "T23:59:59.999999")
    ).fetchone()[0])


def capacity_plan(published_today, requested_per_run=10, approved_per_run=10,
                  target_per_day=DAILY_PUBLISHING_TARGET):
    """Generate an explicit, no-surprise per-run spending limit and useful metrics."""
    target = positive_int(target_per_day, DAILY_PUBLISHING_TARGET)
    approved = positive_int(approved_per_run, DEFAULT_APPROVED_AI_PER_RUN)
    requested = max(0, int(requested_per_run))
    done = max(0, int(published_today))
    remaining = max(0, target - done)
    # A failed AI attempt still costs money; the cap is based on calls,
    # not on the number of articles that happen to pass editorial review.
    actual_limit = min(requested, approved, remaining)
    return {
        "daily_target": target,
        "published_today": done,
        "remaining_to_target": remaining,
        "requested_ai_per_run": requested,
        "approved_ai_per_run": approved,
        "effective_max_ai": actual_limit,
        "api_scaling_requires_approval": approved <= DEFAULT_APPROVED_AI_PER_RUN,
        "desired_average_publications_per_run": (target + RUNS_PER_DAY - 1) // RUNS_PER_DAY,
    }
