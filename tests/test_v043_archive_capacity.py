"""Archive capacity regression: seven days at 100 stories/day needs >=700 slots."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_hungarian_export_does_not_cut_off_seven_day_target():
    source = (ROOT / "orbisacta.py").read_text(encoding="utf-8")
    match = re.search(r"ORDER BY importance DESC, published_utc DESC LIMIT (\d+)", source)
    assert match, "Hungarian archive query missing"
    assert int(match.group(1)) >= 700


def test_translated_archives_have_same_capacity():
    source = (ROOT / "international.py").read_text(encoding="utf-8")
    match = re.search(r"ORDER BY a.importance DESC, a.published_utc DESC LIMIT (\d+)", source)
    assert match, "Multilingual archive query missing"
    assert int(match.group(1)) >= 700


def test_publication_smoke_check_before_and_after_deploy():
    source = (ROOT / ".github/workflows/orbisacta-online.yml").read_text(encoding="utf-8")
    assert "publication_health.py local --folder docs" in source
    assert "publication_health.py remote --base" in source
    assert "--max-ai 40 --daily-target 100 --max-translations 25" in source
