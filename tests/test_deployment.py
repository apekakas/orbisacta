from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pages_workflow_uses_real_test_runner():
    workflow = (ROOT / ".github/workflows/orbisacta-online.yml").read_text(encoding="utf-8")
    assert "python -m pytest -q tests/" in workflow
    assert "python -m unittest discover" not in workflow
    assert "actions/deploy-pages@" in workflow
    assert "actions/upload-pages-artifact@" in workflow
    assert "secrets.OPENAI_API_KEY" in workflow
    assert "schedule:" in workflow


def test_no_sensitive_internal_preview_in_pages():
    assert (ROOT / "docs/index.html").exists()
    assert (ROOT / "docs/news.json").exists()
    assert not (ROOT / "docs/internal-preview.json").exists()
