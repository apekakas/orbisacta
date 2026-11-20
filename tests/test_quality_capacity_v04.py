"""Offline v0.4 capacity and safety tests. No API/network calls."""
import sqlite3
from datetime import datetime, timezone

from quality_capacity import capacity_plan, daily_published_count, positive_int


def test_default_cap_does_not_increase_spend():
    p = capacity_plan(0, requested_per_run=40, approved_per_run=10)
    assert p["daily_target"] == 100
    assert p["effective_max_ai"] == 10
    assert p["desired_average_publications_per_run"] == 25
    assert p["api_scaling_requires_approval"]


def test_explicit_approval_allows_higher_limit_but_not_above_target():
    p = capacity_plan(96, requested_per_run=40, approved_per_run=40)
    assert p["effective_max_ai"] == 4
    assert p["remaining_to_target"] == 4


def test_target_reached_stops_calls():
    assert capacity_plan(100, 50, 50)["effective_max_ai"] == 0
    assert capacity_plan(110, 50, 50)["effective_max_ai"] == 0


def test_malformed_approval_falls_back_to_safe_cap():
    assert positive_int("not-a-number", 10) == 10
    assert positive_int("-99", 10) == 10
    assert capacity_plan(0, 0, 10)["effective_max_ai"] == 0


def test_published_today_uses_approval_day_not_article_day():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE articles (status TEXT, processed_utc TEXT)")
    con.executemany("INSERT INTO articles VALUES (?, ?)", [
        ("published", "2026-11-20T00:00:00+00:00"),
        ("published", "2026-11-20T22:00:00+00:00"),
        ("published", "2026-11-19T23:59:59+00:00"),
        ("needs_review", "2026-11-20T10:00:00+00:00"),
    ])
    at = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
    assert daily_published_count(con, at) == 2
    con.close()
