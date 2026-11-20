"""Reader-comprehension quality indicators are nonblocking heuristics."""
from datetime import datetime, timezone
from hungarian_language import jargon_review_terms, polish_hungarian
from quality_metrics import publishable_metrics


def sample(summary, *, context="", country="EU", topic="gazdaság"):
    return dict(
        title_hu="Új európai kutatási adatok",
        summary_hu=summary,
        context_text=context,
        country=country,
        topic=topic,
        published_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_name="Official source",
    )


def report(articles):
    now = datetime.now(timezone.utc).date().isoformat()
    archive = {"start_date": now, "end_date": now, "days": 7, "timezone": "UTC"}
    return publishable_metrics(
        articles, {"EU": "Európai Unió"}, ["gazdaság", "tudomány"],
        archive, datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def test_known_specialist_terms_flagged_for_review():
    assert "depriváció" in jargon_review_terms("A deprivációs ráta 6,3% volt.")
    assert "incidencia" in jargon_review_terms("Az incidencia emelkedett.")
    assert "masztektómia" in jargon_review_terms("A masztektómiák száma nőtt.")
    assert jargon_review_terms("A nők 6,3%-a élt súlyos nélkülözésben.") == []
    assert jargon_review_terms(None) == []


def test_plain_language_copyedit_reduces_flags():
    raw = "A súlyos anyagi és társadalmi deprivációs ráta 6,3% volt."
    assert jargon_review_terms(raw)
    assert not jargon_review_terms(polish_hungarian(raw))


def test_quality_dashboard_summary_counts_without_blocking_or_republishing():
    data = [
        sample("A jelentés szerint a deprivációs ráta 6,3% volt."),
        sample("Az incidencia 3%-kal nőtt.", context="Az incidencia új eseteket mér."),
        sample("A háztartások 6,3%-a súlyos nélkülözésben élt."),
    ]
    quality = report(data)
    assert quality["total"]["published"] == 3
    assert quality["total"]["readability_review_candidates"] == 2
    assert quality["total"]["readability_without_separate_explainer"] == 1
    assert quality["countries"]["EU"]["readability_review_candidates"] == 2
    assert quality["topics"]["gazdaság"]["readability_review_candidates"] == 2
    assert "not proof" in quality["measurement"]["readability_review_candidates"]
    assert "within the five sentences" in quality["measurement"]["readability_without_separate_explainer"]


def test_other_languages_and_source_material_not_scanned():
    data = [sample("A lakosság 6,3%-a nélkülözésben élt.", context="depriváció: szakkifejezés")]
    quality = report(data)
    assert quality["total"]["readability_review_candidates"] == 0
