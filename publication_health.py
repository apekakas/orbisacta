"""OrbisActa publication smoke checks (standard library, no API billing).

Checks JSON schema and publication freshness, not journalistic factual accuracy.
Usage:
  python publication_health.py local --folder docs
  python publication_health.py remote --base https://example.github.io/orbisacta/
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
import time
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return stamp.astimezone(timezone.utc)


def verify_publication(status, news, quality, at=None, max_age_hours=3, expected_updated=None):
    """Validate structural consistency, freshness and operational status."""
    now = at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("test time requires timezone")
    published_time = parse_timestamp(status.get("updated_utc"))
    if expected_updated is not None and published_time != parse_timestamp(expected_updated):
        raise ValueError("deployed version does not match this workflow run")
    age = now.astimezone(timezone.utc) - published_time
    if age > timedelta(hours=max_age_hours) or age < timedelta(minutes=-5):
        raise ValueError("publication status is stale or future-dated")
    if status.get("project") != "OrbisActa" or news.get("project") != "OrbisActa":
        raise ValueError("unexpected project")
    articles = news.get("articles")
    if not isinstance(articles, list):
        raise ValueError("news articles must be a list")
    if news.get("count") != len(articles):
        raise ValueError("news article count differs from array size")
    if status.get("live_article_count") != len(articles):
        raise ValueError("status article count differs from published data")
    if quality.get("total", {}).get("published") != len(articles):
        raise ValueError("quality report disagrees with published articles")
    if not isinstance(status.get("feed_count"), int) or not isinstance(status.get("feeds_ok"), int):
        raise ValueError("missing RSS diagnostics")
    if not (0 <= status["feeds_ok"] <= status["feed_count"]):
        raise ValueError("invalid working RSS feed count")
    if not isinstance(status.get("items_published_in_run"), int):
        raise ValueError("missing publication metric")
    if not isinstance(status.get("ai_configured"), bool):
        raise ValueError("missing AI status")
    return {
        "updated_utc": published_time.isoformat(),
        "feeds_working": status["feeds_ok"],
        "feeds_checked": status["feed_count"],
        "published_in_run": status["items_published_in_run"],
        "published_in_archive": len(articles),
        "ai_configured": status["ai_configured"],
        "daily_target": status.get("daily_target"),
        "published_today": status.get("published_today"),
        "warning": (
            "No published articles: inspect API key, source extraction and QA errors"
            if not articles else
            "No RSS feeds succeeded" if status["feeds_ok"] == 0 else None
        ),
    }


def read_local(folder):
    base = Path(folder)
    return tuple(json.loads((base / name).read_text(encoding="utf-8"))
                 for name in ("site-status.json", "news.json", "quality.json"))


def read_remote(base, cache_key):
    def load(name):
        url = urljoin(base.rstrip("/") + "/", name) + "?check=" + cache_key
        req = Request(url, headers={"User-Agent": "OrbisActa-Deployment-Health/0.4"})
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    return tuple(load(name) for name in
                 ("site-status.json", "news.json", "quality.json"))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("local", "remote"))
    parser.add_argument("--folder", default="docs")
    parser.add_argument("--base", default="")
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--expected-updated", default=None,
                        help="Exact UTC timestamp from the freshly built local site-status.json")
    args = parser.parse_args(argv)
    if args.mode == "remote" and not args.base.startswith("https://"):
        parser.error("--base requires an HTTPS URL")
    tries = max(1, args.retries if args.mode == "remote" else 1)
    for attempt in range(tries):
        try:
            values = (read_local(args.folder) if args.mode == "local" else
                      read_remote(args.base, str(int(time.time()))))
            result = verify_publication(*values, expected_updated=args.expected_updated)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f"Publication check {attempt + 1}/{tries} failed: {type(exc).__name__}: {exc}")
            if attempt + 1 < tries:
                time.sleep(8)
    return 1


if __name__ == "__main__":
    sys.exit(main())
