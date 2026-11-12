import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import orbisacta as oa

RSS = b'''<?xml version="1.0"?><rss version="2.0"><channel><title>Test</title>
<item><title>Economy &amp; markets</title><link>https://example.org/a?utm_source=x</link>
<description>Market description</description><pubDate>Thu, 12 Nov 2026 12:00:00 GMT</pubDate></item>
</channel></rss>'''
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
    assert rss[0]['published_utc'].startswith('2026-11-12')
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
    assert 10 <= len(sources) <= 20
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
