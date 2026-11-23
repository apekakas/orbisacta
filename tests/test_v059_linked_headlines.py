"""Source-linked headlines help feed cadence without pretending to be verified briefs."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import orbisacta as oa
from source_headlines import export_linked_headlines, linked_headlines


def entry(url, title, hours_ago=0):
    return {
        "url": url, "title": title,
        "published_utc": (
            datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        ).isoformat(timespec="seconds")
    }


def source(sid="licensed", *, approved=True):
    return {
        "id": sid, "name": "Original verified source", "country": "EU",
        "topic_hint": "gazdaság", "ai_approved": approved, "enabled": True,
        "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "rights_reference_url": "https://example.org/rights"
    }


def test_pending_and_reviewed_linked_headlines_are_distinct_from_published(tmp_path):
    con = oa.connect(tmp_path / "db.sqlite3")
    s=source()
    entries=[
        entry("https://example.org/new", "New original-language source headline"),
        entry("https://example.org/review", "Recent news from a known source"),
        entry("https://example.org/published", "Validated and summarized article"),
        entry("https://example.org/other-country", "Ambiguous target-country article"),
        entry("https://example.org/old", "Old title not from recent days", 300),
    ]
    oa.insert_entries(con, s, entries)
    con.execute("UPDATE articles SET status='needs_review' WHERE url=?", (entries[1]["url"],))
    con.execute("UPDATE articles SET status='published' WHERE url=?", (entries[2]["url"],))
    con.execute("UPDATE articles SET status='wrong_country' WHERE url=?", (entries[3]["url"],))
    con.commit()
    result=linked_headlines(con,[s],oa.archive_window())
    urls={item["url"] for item in result}
    assert urls == {entries[0]["url"],entries[1]["url"],entries[3]["url"]}
    assert next(x for x in result if x["url"]==entries[3]["url"])["country"]=="WORLD"
    assert all("summary_hu" not in x and "excerpt" not in x and "status" not in x for x in result)
    out=tmp_path/"headlines.json"
    assert export_linked_headlines(con,[s],oa.archive_window(),out)==3
    data=json.loads(out.read_text(encoding="utf-8"))
    assert data["type"]=="unverified_source_headlines"
    assert data["count"]==3
    con.close()


def test_rights_unapproved_sources_and_missing_dates_never_exposed(tmp_path):
    con=oa.connect(tmp_path/"db.sqlite3")
    approved=source()
    denied=source("restricted",approved=False)
    oa.insert_entries(con,approved,[entry("https://example.org/undated","No publish date")])
    con.execute("UPDATE articles SET published_utc=''")
    oa.insert_entries(con,denied,[entry("https://example.org/private","Not permitted for AI")])
    con.commit()
    assert linked_headlines(con,[approved,denied],oa.archive_window())==[]
    con.close()


def test_regular_export_includes_linked_headlines_but_never_as_verified_news(tmp_path,monkeypatch):
    con=oa.connect(tmp_path/"db.sqlite3")
    s=source()
    oa.insert_entries(con,s,[entry("https://example.org/pending","Pending approved source headline")])
    monkeypatch.setattr(oa,"load_sources",lambda *args:[s])
    out=tmp_path/"docs"/"news.json"
    assert oa.export_json(con,out)==0
    assert json.loads(out.read_text(encoding="utf-8"))["count"]==0
    linked=json.loads((out.parent/"headlines.json").read_text(encoding="utf-8"))
    assert linked["count"]==1
    assert linked["articles"][0]["title_original"]=="Pending approved source headline"
    con.close()


def test_all_six_pages_load_separate_source_headlines_feed():
    root=Path(__file__).resolve().parents[1]/"docs"
    code=(root/"assets"/"source-headlines.js").read_text(encoding="utf-8")
    assert 'payload.type!=="unverified_source_headlines"' in code
    assert '"./headlines.json"' in code
    for lang in ("hu","en","de","fr","es","pt"):
        page=(root/lang/"index.html").read_text(encoding="utf-8")
        assert 'id="source-headlines"' in page
        assert './assets/source-headlines.js' in page
        assert 'id="feed"' in page
