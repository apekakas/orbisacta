import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import orbisacta as oa

# The simulated story must be fresh for the 7-day editorial cutoff.
# Use dynamic fixture dates so CI doesn't start failing a week after creation.
TEST_DATE = format_datetime(datetime.now(timezone.utc), usegmt=True)
RSS = f'''<?xml version="1.0"?><rss version="2.0"><channel><title>Test</title>
<item><title>Economy &amp; markets</title><link>https://example.org/a?utm_source=x</link>
<description>Market description</description><pubDate>{TEST_DATE}</pubDate></item>
</channel></rss>'''.encode('utf-8')
ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>New item</title>
<link rel="alternate" href="https://example.org/b"/><updated>2026-11-12T13:10:00Z</updated>
<summary>Atom desc</summary></entry></feed>'''
SRC = {'id': 'demo', 'name': 'Offline demo', 'country': 'HU', 'topic_hint': 'gazdaság',
       'ai_approved': True, 'rss_url': 'https://example.org/feed'}

def test_rss_and_atom_parsers():
    rss = oa.parse_feed(RSS)
    assert len(rss) == 1
    assert rss[0]['url'] == 'https://example.org/a'
    assert rss[0]['title'] == 'Economy & markets'
    assert rss[0]['published_utc'] == oa.parse_date(TEST_DATE)
    assert oa.parse_feed(ATOM)[0]['url'] == 'https://example.org/b'

def test_deduplicate_and_rights(tmp_path):
    con = oa.connect(tmp_path / 'db.sqlite3')
    source = dict(SRC, ai_approved=False)
    entries = oa.parse_feed(RSS)
    assert oa.insert_entries(con, source, entries)['new'] == 1
    assert oa.insert_entries(con, source, entries)['duplicates'] == 1
    assert con.execute('SELECT status FROM articles').fetchone()[0] == 'awaiting_rights'
    con.close()

def test_exactly_five_supported_facts():
    text = 'A local sample contains a factual claim about business. ' * 22
    quote = 'A local sample contains a factual claim about business.'
    points = [{'sentence_hu': f'A cikk {n}. külön üzleti témájáról számol be Magyarországon.',
               'support_quote': quote} for n in range(1,6)]
    assert oa.check_evidence(text, points) == (True, 'ok')
    assert oa.check_evidence(text, points[:4])[0] is False
    assert oa.check_evidence(text, [{**p,'support_quote':'invented evidence not in source'} for p in points])[0] is False

def test_export_only_published(tmp_path):
    con = oa.connect(tmp_path / 'db.sqlite3')
    oa.insert_entries(con, SRC, oa.parse_feed(RSS))
    target = tmp_path / 'out.json'
    assert oa.export_json(con, target) == 0
    con.execute("UPDATE articles SET status='published', title_hu='Próbahír', summary_hu='Öt ellenőrzött mondat.', topic='gazdaság'")
    con.commit()
    assert oa.export_json(con, target) == 1
    assert json.loads(target.read_text())['articles'][0]['title_hu'] == 'Próbahír'
    con.close()

def test_e2e_offline_mocked_ai(tmp_path, monkeypatch):
    con = oa.connect(tmp_path / 'db.sqlite3')
    oa.insert_entries(con, SRC, oa.parse_feed(RSS))
    original = 'A sample story explicitly states a test fact.'
    text = (original + ' More test details.') * 24
    points = [{'sentence_hu': f'Ez a(z) {n} sorszámú ellenőrzött, magyar nyelvű tesztmondat a cikk tényéről.',
               'support_quote': original} for n in range(1,6)]
    monkeypatch.setenv('OPENAI_API_KEY','offline-fake')
    monkeypatch.setattr(oa, 'extract_article_text', lambda url: text)
    monkeypatch.setattr(oa, 'ai_summarize', lambda row, text, model: {
        'country_relevant':True, 'title_hu':'Teszthír', 'topic':'gazdaság',
        'importance':75, 'points':points})
    result = oa.process(con, [SRC], 1, 'mock')
    assert result['published'] == 1
    assert oa.export_json(con, tmp_path/'out.json') == 1
    assert len(con.execute('SELECT summary_hu FROM articles').fetchone()[0].split('. ')) == 5
    con.close()

def test_internal_preview_keeps_rights_status(tmp_path):
    con = oa.connect(tmp_path / 'db.sqlite3')
    oa.insert_entries(con, dict(SRC, ai_approved=False), oa.parse_feed(RSS))
    preview = oa.internal_preview(con)
    assert preview['internal_only'] is True
    assert preview['items'][0]['status'] == 'awaiting_rights'
    assert 'url' in preview['items'][0]
    con.close()


def test_author_and_license_preservation(tmp_path):
    source = dict(SRC, author_required=True, license='CC BY 3.0',
                  license_url='https://creativecommons.org/licenses/by/3.0/',
                  rights_reference_url='https://example.org/policy')
    with_author = RSS.replace(b'<description>', b'<dc:creator>Example Author</dc:creator><description>')\
        .replace(b'<rss version="2.0">', b'<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">')
    con = oa.connect(tmp_path / 'db.sqlite3')
    oa.insert_entries(con,source,oa.parse_feed(with_author))
    record = con.execute('SELECT author, license, license_url FROM articles').fetchone()
    assert record['author'] == 'Example Author'
    assert record['license'] == 'CC BY 3.0'
    assert 'creativecommons.org' in record['license_url']
    con.close()


def test_author_missing_blocks_ai(tmp_path, monkeypatch):
    source = dict(SRC, author_required=True)
    con = oa.connect(tmp_path / 'db.sqlite3')
    oa.insert_entries(con,source,oa.parse_feed(RSS))
    monkeypatch.setenv('OPENAI_API_KEY','fake')
    monkeypatch.setattr(oa,'extract_article_text',lambda _: (_ for _ in ()).throw(AssertionError('cannot fetch before author check')))
    assert oa.process(con,[source],1,'mock')['published'] == 0
    result = con.execute('SELECT status,error FROM articles').fetchone()
    assert result['status']=='needs_review' and 'author_missing' in result['error']
    con.close()


def test_world_country_assignment(tmp_path, monkeypatch):
    source = dict(SRC,country='WORLD')
    con = oa.connect(tmp_path / 'db.sqlite3')
    oa.insert_entries(con,source,oa.parse_feed(RSS))
    quote='A sample story explicitly states a test fact.'
    text=(quote+' More test details.')*25
    monkeypatch.setenv('OPENAI_API_KEY','fake')
    monkeypatch.setattr(oa,'extract_article_text',lambda _:text)
    monkeypatch.setattr(oa,'ai_summarize',lambda *a: {
        'country_relevant':True,'event_country':'DE','title_hu':'Próbafordítás',
        'topic':'politika','importance':45,
        'points':[{'sentence_hu':f'A {n}. ellenőrzött mondat különbözik a többi mondattól.',
                   'support_quote':quote} for n in range(1,6)]})
    assert oa.process(con,[source],1,'mock')['published']==1
    assert con.execute('SELECT country FROM articles').fetchone()[0]=='DE'
    con.close()


def test_config_sources_and_license_links():
    sources = oa.load_sources()
    assert 19 <= len(sources) <= 30
    assert any(s['topic_hint']=='sport' for s in sources)
    assert any(s['country']=='HU' for s in sources)
    assert any(s['country']=='DE' for s in sources)
    assert any(s['country']=='US' for s in sources)
    assert all(s.get('rights_reference_url') for s in sources if s['ai_approved'])


def test_database_migration_from_v01(tmp_path):
    import sqlite3
    db=tmp_path/'legacy.sqlite3'
    legacy=sqlite3.connect(db)
    legacy.execute("""CREATE TABLE articles (
        id TEXT PRIMARY KEY, country TEXT NOT NULL, topic_hint TEXT NOT NULL,
        source_id TEXT NOT NULL, source_name TEXT NOT NULL,
        title_original TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
        published_utc TEXT, excerpt TEXT, text_excerpt TEXT,
        title_hu TEXT, summary_hu TEXT, topic TEXT,
        importance INTEGER DEFAULT 0, status TEXT NOT NULL,
        error TEXT, ingested_utc TEXT NOT NULL, processed_utc TEXT)""")
    legacy.commit(); legacy.close()
    upgraded=oa.connect(db)
    cols={x[1] for x in upgraded.execute('PRAGMA table_info(articles)')}
    assert {'author','license','license_url','rights_reference_url'}<=cols
    upgraded.close()

def test_diverse_ai_selection_balances_countries():
    rows = [
        {'id': 'us-1', 'country': 'US', 'published_utc': '2026-11-19T17:00:00+00:00'},
        {'id': 'us-2', 'country': 'US', 'published_utc': '2026-11-19T16:00:00+00:00'},
        {'id': 'us-3', 'country': 'US', 'published_utc': '2026-11-19T15:00:00+00:00'},
        {'id': 'hu-1', 'country': 'HU', 'published_utc': '2026-11-19T14:00:00+00:00'},
        {'id': 'jp-1', 'country': 'JP', 'published_utc': '2026-11-19T13:00:00+00:00'},
    ]
    assert [r['id'] for r in oa.select_diverse_pending(rows, 4)] == [
        'us-1', 'hu-1', 'jp-1', 'us-2'
    ]


def test_new_country_sources_are_registered():
    sources = oa.load_sources()
    ids = {s['country'] for s in sources}
    assert {'FR', 'IT', 'JP', 'BR'} <= ids
    assert all(s['ai_approved'] for s in sources if s['country'] in {'FR', 'IT', 'JP', 'BR'})


def test_multilingual_translation_validate_and_export(tmp_path):
    import international as il
    db = oa.connect(tmp_path / 'multi.sqlite3')
    oa.insert_entries(db, SRC, oa.parse_feed(RSS))
    db.execute("""UPDATE articles SET status='published', title_hu='Magyar cím az olvasóknak',
                 summary_hu='Egy. Kettő. Három. Négy. Öt.'""")
    db.commit()
    out = tmp_path / 'news.json'
    assert oa.export_json(db, out) == 1
    assert json.loads((tmp_path / 'news-en.json').read_text())['count'] == 0
    translated = {lang: {'title': f'Proper translated headline for {lang}',
                         'sentences': [f'The translated verified fact number {i} for {lang}.' for i in range(1,6)]}
                  for lang in il.TARGET_LANGUAGES}
    valid = il.validate_translations(translated)
    news_id = db.execute("SELECT id FROM articles").fetchone()[0]
    for lang, (title, summary) in valid.items():
        db.execute("""INSERT INTO article_translations
            (article_id, lang, title, summary, translated_utc)
            VALUES (?, ?, ?, ?, ?)""", (news_id, lang, title, summary, oa.now_utc()))
    db.commit()
    assert oa.export_json(db, out) == 1
    en = json.loads((tmp_path / 'news-en.json').read_text())
    assert en['language'] == 'en' and en['count'] == 1
    assert en['articles'][0]['url'] == 'https://example.org/a'
    assert en['articles'][0]['title_hu'] == 'Proper translated headline for en'
    assert json.loads(out.read_text())['articles'][0]['title_hu'] == 'Magyar cím az olvasóknak'
    db.close()


def test_translation_rejects_duplicated_or_missing_sentences():
    import international as il
    bad = {lang: {'title': 'Properly long news headline',
                  'sentences': ['The repeated sentence has some meaningful length.'] * 5}
           for lang in il.TARGET_LANGUAGES}
    try:
        il.validate_translations(bad)
        assert False, 'Duplicates must be rejected'
    except ValueError:
        pass
    assert tuple(il.LANGUAGES) == ('hu', 'en', 'es', 'fr', 'de', 'pt')


def test_translation_cap_zero_does_not_use_api(tmp_path, monkeypatch):
    import international as il
    db = oa.connect(tmp_path / 'cap.sqlite3')
    monkeypatch.setenv('OPENAI_API_KEY', 'offline-fake')
    assert il.translate_pending(db, 0)['attempted'] == 0
    db.close()


def test_international_static_pages_and_dormant_advertising():
    import international as il
    assert set(il.LANGUAGES) == {"hu", "en", "es", "fr", "de", "pt"}
    root = Path(__file__).resolve().parents[1] / "docs"
    for lang in il.LANGUAGES:
        html_page = (root / lang / "index.html").read_text(encoding="utf-8")
        assert '<html lang="' + lang + '">' in html_page
        assert '<base href="../"/>' in html_page
        assert "ORBIS_PAGE_LANG" in html_page
    for path in ("assets/i18n.js", "assets/globe.js", "ads-config.json", "sitemap.xml"):
        assert (root / path).is_file()
    config = json.loads((root / "ads-config.json").read_text(encoding="utf-8"))
    assert config["enabled"] is False
    assert config["adScriptsAllowed"] is False
    page = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-ad-slot="top-banner" hidden' in page
    assert 'data-ad-slot="in-feed" hidden' in page
    assert "googlesyndication.com" not in page


def test_source_diversity_prefers_recent_alternate_publisher():
    from datetime import datetime, timezone, timedelta
    d=datetime.now(timezone.utc)
    stamp=lambda hours: (d-timedelta(hours=hours)).isoformat(timespec="seconds")
    articles=[
        {"id":"nasa-1","country":"US","source_id":"nasa-news","published_utc":stamp(1)},
        {"id":"nasa-2","country":"US","source_id":"nasa-news","published_utc":stamp(2)},
        {"id":"noaa-1","country":"US","source_id":"noaa-news","published_utc":stamp(3)},
        {"id":"nasa-old","country":"US","source_id":"nasa-news","published_utc":stamp(50)},
    ]
    picked=oa.select_diverse_pending(articles,3)
    assert [item["id"] for item in picked] == ["nasa-1","noaa-1","nasa-2"]


def test_source_diversity_never_promotes_very_old_source():
    from datetime import datetime, timezone, timedelta
    d=datetime.now(timezone.utc)
    stamp=lambda hours: (d-timedelta(hours=hours)).isoformat(timespec="seconds")
    articles=[
        {"id":"nasa-1","country":"US","source_id":"nasa-news","published_utc":stamp(1)},
        {"id":"nasa-2","country":"US","source_id":"nasa-news","published_utc":stamp(2)},
        {"id":"other-old","country":"US","source_id":"noaa-news","published_utc":stamp(100)},
    ]
    assert [item["id"] for item in oa.select_diverse_pending(articles,2)]==["nasa-1","nasa-2"]


def test_science_sources_from_multiple_publishers():
    sources=oa.load_sources()
    groups={item["publisher"] for item in sources
            if item["topic_hint"]=="tudomány" and item["ai_approved"]}
    assert {"NASA","NOAA","National Institutes of Health","Public Library of Science (PLOS)"}<=groups
