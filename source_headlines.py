"""Source-headline feed for incoming stories not yet published as AI briefs.

This is NOT a summary and never presented as an editorially verified article.
Only approved RSS sources with trustworthy recent dates, URLs and titles.
No source article text, excerpts, personal data or invented translations.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
import json


def linked_headlines(con, sources, archive, *, limit=120):
    approved = {str(s["id"]) for s in sources
                if s.get("enabled", True) and s.get("ai_approved") is True}
    if not approved:
        return []
    cutoff = archive["cutoff_utc"]
    tomorrow = (datetime.fromisoformat(archive["end_date"]).date()
                + timedelta(days=1)).isoformat() + "T00:00:00+00:00"
    placeholders = ",".join("?" for _ in approved)
    rows = con.execute(
        f"""SELECT id, title_original, url, source_name, source_id,
                   country, topic_hint, published_utc, status
            FROM articles
            WHERE published_utc >= ? AND published_utc < ?
              AND source_id IN ({placeholders})
              AND status IN ('pending_ai','needs_review','wrong_country')
            ORDER BY published_utc DESC LIMIT ?""",
        (cutoff, tomorrow, *sorted(approved), max(0, limit * 3)),
    ).fetchall()
    result, seen = [], set()
    for row in rows:
        item = dict(row)
        # Never claim a country based on a known-rejected classification.
        if item["status"] == "wrong_country":
            item["country"] = "WORLD"
        parsed = urlsplit(item["url"] or "")
        title = (item["title_original"] or "").strip()
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            continue
        if not title or len(title) > 350 or item["url"] in seen:
            continue
        try:
            date = datetime.fromisoformat(item["published_utc"].replace("Z", "+00:00"))
            if not date.tzinfo or date > datetime.now(timezone.utc) + timedelta(hours=2):
                continue
        except (ValueError, TypeError):
            continue
        seen.add(item["url"])
        result.append({
            "title_original": title,
            "url": item["url"],
            "source_name": item["source_name"],
            "country": item["country"],
            "published_utc": item["published_utc"],
        })
        if len(result) >= limit:
            break
    return result


def export_linked_headlines(con, sources, archive, destination):
    articles = linked_headlines(con, sources, archive)
    data = {
        "project": "OrbisActa",
        "type": "unverified_source_headlines",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "disclaimer": "Original-language linked headlines from attributed sources. Not verified or rewritten by OrbisActa.",
        "count": len(articles),
        "articles": articles,
    }
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(articles)
