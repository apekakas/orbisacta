"""Editorially conservative near-duplicate matching.

Related stories with similar titles may be genuine updates. Only suppress
near-identical same-source headlines published close together. Exact
headlines may still be separate dated developments after several days.
"""
from datetime import datetime, timezone
from difflib import SequenceMatcher
import re
import unicodedata


def title_key(text):
    return re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", text or "").lower()).strip()


def aware_date(text):
    if not text:
        return None
    try:
        stamp = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        if stamp.tzinfo is not None and stamp.utcoffset() is not None:
            return stamp.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def is_likely_duplicate(new_title, new_stamp, prior_title, prior_stamp):
    """Missing or unreliable dates must not suppress a different URL."""
    current = aware_date(new_stamp)
    previous = aware_date(prior_stamp)
    if current is None or previous is None:
        return False
    a, b = title_key(new_title), title_key(prior_title)
    if not a or not b:
        return False
    distance_hours = abs((current - previous).total_seconds()) / 3600
    if a == b:
        return distance_hours <= 48
    # Require very high similarity *and* publication on essentially the
    # same news cycle, to avoid silently dropping follow-ups and updates.
    return distance_hours <= 12 and SequenceMatcher(None, a, b).ratio() >= 0.985
