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
    assert {'author','license','license_url','rights_reference_url','context_hu'}<=cols
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
    for lang, (title, summary, context) in valid.items():
        db.execute("""INSERT INTO article_translations
            (article_id, lang, title, summary, context_text, translated_utc)
            VALUES (?, ?, ?, ?, ?, ?)""", (news_id, lang, title, summary, context, oa.now_utc()))
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


def test_modern_mobile_controls_and_six_locale_pages():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    for lang in ("hu", "en", "es", "fr", "de", "pt"):
        page = (root / lang / "index.html").read_text(encoding="utf-8")
        assert 'id="globe-toggle" aria-controls="globe-section"' in page
        assert "globe-panel:not(.mobile-open)" in page
        assert "countryFlagAssets" in page
        assert "countryAlphabet.compare(a[1],b[1])" in page
        assert 'class="language-menu" id="language"' in page
        assert "topicIcons" in page
        assert "sortOrder='featured'" in page
        assert "tr(expanded?'hideGlobe':'showGlobe')" in page
    root_page = (root / "index.html").read_text(encoding="utf-8")
    assert 'data-language="hu" href="./hu/"' in root_page
    assert 'data-language="en" href="./en/"' in root_page
    assert 'data-language="pt" href="./pt/"' in root_page
    assert 'id="current-language-flag"' in root_page
    translations = (root / "assets" / "i18n.js").read_text(encoding="utf-8")
    assert translations.count("featured:") == 6
    assert translations.count("showGlobe:") == 6
    assert translations.count("hideGlobe:") == 6

def test_svg_flags_and_language_dependent_country_sorting():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    for code in ("hu", "gb", "es", "fr", "de", "br", "it", "jp", "us", "eu"):
        svg = (root / "assets" / "flags" / (code+".svg")).read_text(encoding="utf-8")
        assert svg.startswith("<svg") and "<script" not in svg
    assert "MIT License" in (root / "assets" / "flags" / "LICENSE.txt").read_text(encoding="utf-8")
    for code in ("hu", "en", "es", "fr", "de", "pt"):
        page = (root / code / "index.html").read_text(encoding="utf-8")
        assert "countryAlphabet.compare(a[1],b[1])" in page
        assert 'src="./assets/flags/gb.svg"' in page
        assert 'src="./assets/flags/br.svg"' in page


def test_statistics_must_be_present_in_two_supported_hungarian_facts():
    from editorial_quality import check_numeric_facts
    source = (
        "The labour force report found an unemployment rate of 4.6 percent "
        "in 2026 and an employment rate of 72.3 percent among working-age residents. "
        "The office published the latest comparison to the previous period."
    )
    original = [
        {"sentence_hu": "A munkanélküliségi ráta 4,6 százalékot ért el a vizsgált időszakban.",
         "support_quote": "an unemployment rate of 4.6 percent"},
        {"sentence_hu": "A foglalkoztatottsági ráta 72,3 százalék volt a munkaképes korúaknál.",
         "support_quote": "an employment rate of 72.3 percent"},
    ]
    assert check_numeric_facts(source, original) == (True, "ok")
    vague = [
        {"sentence_hu": "A jelentés a munkanélküliség alakulását ismerteti.",
         "support_quote": "an unemployment rate of 4.6 percent"},
        {"sentence_hu": "A cikk a foglalkoztatás mutatóit is bemutatja.",
         "support_quote": "an employment rate of 72.3 percent"},
    ]
    assert check_numeric_facts(source, vague)[0] is False
    unsupported = [
        {"sentence_hu": "A munkanélküliség 9,7 százalékot ért el.",
         "support_quote": "an unemployment rate of 4.6 percent"},
        original[1],
    ]
    assert check_numeric_facts(source, unsupported)[0] is False


def test_years_dates_are_not_counted_as_two_statistics():
    from editorial_quality import check_numeric_facts
    source = "This report was published on 2026-11-19 and compares 2025 with 2026."
    assert check_numeric_facts(source, [])[0] is True


def test_country_glossary_requires_exact_source_support_and_two_sentence_maximum():
    from editorial_quality import validated_background
    source = (
        "The PAYE scheme requires employers to deduct income tax directly "
        "from workers' salaries. The council tax is a local property-based "
        "tax used to finance municipal services in the United Kingdom."
    )
    items = [
        {"term_original": "PAYE",
         "support_quote": "The PAYE scheme requires employers to deduct income tax directly from workers' salaries.",
         "explanation_hu": "A PAYE egy brit adólevonási rendszer, amelyben a munkáltató közvetlenül a munkabérből vonja le a jövedelemadót."},
        {"term_original": "council tax",
         "support_quote": "The council tax is a local property-based tax used to finance municipal services in the United Kingdom.",
         "explanation_hu": "A council tax az Egyesült Királyságban alkalmazott helyi, ingatlanalapú adó, amelyből önkormányzati szolgáltatásokat finanszíroznak."},
        {"term_original": "invented programme",
         "support_quote": "A fabricated quotation not in the original article.",
         "explanation_hu": "Ez a forrásban nem szereplő, ezért nem közölhető fogalom."},
    ]
    valid = validated_background(source, items)
    assert "PAYE" in valid and "council tax" in valid
    assert valid.count(".") == 2
    assert validated_background(source, [items[2]]) == ""


def test_country_glossary_translation_and_export(tmp_path):
    import international as il
    con = oa.connect(tmp_path / "context.sqlite3")
    oa.insert_entries(con, SRC, oa.parse_feed(RSS))
    con.execute("""UPDATE articles SET status='published',
                   title_hu='Vizsgálati hír ellenőrzött címmel',
                   summary_hu='Első tény. Második tény. Harmadik tény. Negyedik tény. Ötödik tény.',
                   context_hu='A helyi fogalom rövid értelmezése a forrás szerint.'""")
    con.commit()
    context = ("The country-specific programme is a national scheme for "
               "supporting residents through local public administration.")
    payload = {lang: {
        "title": "Verified international news headline",
        "sentences": [f"This is the verified factual sentence number {i}." for i in range(1,6)],
        "context": context
    } for lang in il.TARGET_LANGUAGES}
    translations = il.validate_translations(payload, "A helyi fogalom értelmezése.")
    article_id = con.execute("SELECT id FROM articles").fetchone()[0]
    for lang, (title, summary, translated_context) in translations.items():
        con.execute("""INSERT INTO article_translations
            (article_id, lang, title, summary, context_text, translated_utc)
            VALUES (?,?,?,?,?,?)""",
            (article_id, lang, title, summary, translated_context, oa.now_utc()))
    con.commit()
    out = tmp_path / "news.json"
    assert oa.export_json(con, out) == 1
    hu = json.loads(out.read_text())["articles"][0]
    en = json.loads((tmp_path / "news-en.json").read_text())["articles"][0]
    assert hu["context_text"].startswith("A helyi fogalom")
    assert en["context_text"] == context
    assert len(en["summary_hu"].split(". ")) == 5
    con.close()


def test_country_glossary_translations_reject_missing_or_extra_sentences():
    import international as il
    payload = {lang: {
        "title": "Verified news story headline",
        "sentences": [f"This is a checked sentence number {i}." for i in range(1,6)],
        "context": ""
    } for lang in il.TARGET_LANGUAGES}
    try:
        il.validate_translations(payload, "Egy magyar háttérmondat.")
        assert False, "Missing translated glossary must be rejected"
    except ValueError:
        pass
    for item in payload.values():
        item["context"] = ("A factual explanation of the local term. "
                           "A second explanation with more factual detail. "
                           "An impermissible third explanatory sentence.")
    try:
        il.validate_translations(payload, "Egy magyar háttérmondat.")
        assert False, "Glossary must be limited to two sentences"
    except ValueError:
        pass


def test_glossary_is_rendered_on_all_six_locale_pages():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    for lang in ("hu", "en", "es", "fr", "de", "pt"):
        page = (root / lang / "index.html").read_text(encoding="utf-8")
        assert "item.context_text" in page
        assert "tr('backgroundTitle')" in page
        assert ".article-context" in page
    dictionary = (root / "assets" / "i18n.js").read_text(encoding="utf-8")
    assert dictionary.count('backgroundTitle:') == 6


def test_six_new_countries_and_source_candidates_are_configured():
    import json
    codes = {"IN", "CN", "AU", "SA", "NG", "ZA"}
    assert codes <= set(oa.COUNTRIES)
    sources = oa.load_sources()
    new = {s["country"]: s for s in sources if s["country"] in codes}
    assert codes == set(new)
    assert all(s["publisher"] == "Global Voices" for s in new.values())
    assert all(s.get("rights_reference_url") and s.get("author_required") for s in new.values())
    assert len(sources) == 28


def test_mobile_country_buttons_wrap_and_zoom_works_on_all_language_pages():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    flags = {"in", "cn", "au", "sa", "ng", "za"}
    for code in flags:
        svg = (root / "assets" / "flags" / (code + ".svg")).read_text(encoding="utf-8")
        assert svg.startswith("<svg") and "<script" not in svg
    for language in ("hu", "en", "es", "fr", "de", "pt"):
        page = (root / language / "index.html").read_text(encoding="utf-8")
        assert "grid-template-columns:repeat(2,minmax(0,1fr))" in page
        assert ".filters #countries button.chip" in page
        assert "overflow-wrap:anywhere" in page
        assert "data-globe-zoom=\"in\"" in page
        assert "data-globe-zoom=\"out\"" in page
        assert "selected.size<10" not in page
        assert "slice(0,10)" not in page
        for country in flags:
            assert "'" + country.upper() + "'" in page


def test_globe_mobile_pinch_and_expanded_regional_navigation():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    code = (root / "assets" / "globe.js").read_text(encoding="utf-8")
    assert "const pointers=new Map()" in code
    assert "pinchDistance" in code
    assert "pointers.size>=2" in code
    assert "data-globe-zoom" in code
    assert "minScale=110,maxScale=560" in code
    assert "africa:[22,0]" in code
    assert "oceania:[135,-25]" in code


def test_compact_filter_panels_and_language_names_across_six_locales():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    for lang in ("hu", "en", "es", "fr", "de", "pt"):
        page = (root / lang / "index.html").read_text(encoding="utf-8")
        assert '<details class="filters-panel" id="filters-panel">' in page
        assert 'id="filters-title"' in page
        assert 'id="filter-current"' in page
        assert 'id="show-news"' in page
        assert "filtersPanel.open=false;" in page
        assert "id=\"current-language-name\"" in page
        assert ".language-picker span{display:none}" not in page
        assert "#current-language-name{display:inline!important" in page
        assert 'id="globe-zoom-level"' in page
        assert 'data-globe-zoom="in"' in page
        assert 'data-globe-zoom="out"' in page
    i18n = (root / "assets" / "i18n.js").read_text(encoding="utf-8")
    assert i18n.count("filtersTitle:") == 6
    assert i18n.count("viewResults:") == 6
    assert i18n.count("countriesShort:") == 6


def test_globe_native_multitouch_and_obvious_mobile_zoom_controls():
    from pathlib import Path
    globe = (Path(__file__).resolve().parents[1] / "docs" / "assets" / "globe.js").read_text(encoding="utf-8")
    assert 'svg.addEventListener("touchstart"' in globe
    assert 'svg.addEventListener("touchmove"' in globe
    assert 'svg.addEventListener("touchend"' in globe
    assert "ev.preventDefault()" in globe
    assert "touchGap(ev.touches)" in globe
    assert 'const initialScale=window.matchMedia("(max-width:680px)").matches?205:192;' in globe
    assert 'button.dataset.globeZoom==="in"?1.4:1/1.4' in globe
    assert 'document.getElementById("globe-zoom-level")' in globe
