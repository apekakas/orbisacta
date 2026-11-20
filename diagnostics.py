"""Private CI diagnostics: aggregate-only reasons for unpublished summaries."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import sqlite3

db_path = Path(__file__).resolve().parent / "data" / "orbisacta.sqlite3"
if not db_path.exists():
    print("Diagnosztika: nincs adatbázis.")
    raise SystemExit(0)
con = sqlite3.connect(db_path)
try:
    statuses = Counter(dict(con.execute("SELECT status, COUNT(*) FROM articles GROUP BY status").fetchall()))
    errors = con.execute("SELECT error FROM articles WHERE status='needs_review'").fetchall()
    from source_failure_diagnostics import source_failure_breakdown, aggregate_failures
    con.row_factory = sqlite3.Row
    per_source = source_failure_breakdown(con)
    source_totals = aggregate_failures(per_source)
    from multilingual_quality import audit_translation_rows
    multilingual_audit = audit_translation_rows(con)
finally:
    con.close()

def classify(message: str) -> str:
    lower = (message or "").lower()
    for keyword, label in (
        ("author_missing", "Hiányzó szerző"),
        ("insufficient_article_text", "Nem elég hosszú forrásszöveg"),
        ("exactly_five_sentences_required", "Hiányos AI összefoglaló"),
        ("short_evidence", "Túl rövid forrásbizonyíték"),
        ("evidence_not_in_article", "Nem egyező forrásbizonyíték"),
        ("duplicate_sentence", "Ismétlődő mondat"),
        ("bad_sentence", "Érvénytelen mondatforma"),
        ("invalid_topic", "Nem megfelelő témakör"),
        ("two_evidenced_numeric_facts_required", "Két fontos számadat nem igazolható"),
        ("meta_description_without_news", "A hír helyett a cikket ismertető mondat"),
        ("ratelimiterror", "API korlát/kvóta"),
        ("insufficient_quota", "API kvóta hiánya"),
        ("authenticationerror", "API hitelesítés"),
        ("permissiondeniederror", "API jogosultság"),
        ("apiconnectionerror", "API hálózati hiba"),
        ("apitimeouterror", "API időtúllépés"),
        ("notfounderror", "API modell nem elérhető"),
        ("jsondecodeerror", "Érvénytelen AI JSON"),
    ):
        if keyword in lower:
            return label
    return "Egyéb ellenőrzési hiba"

print("Állapotok:", dict(statuses))
print("AI ellenőrzési hibaokok:", dict(Counter(classify(x[0]) for x in errors)))
print("Korábbi öt idegen nyelvű fordítás ellenőrzése (összesítés, automatikus módosítás nélkül):",
      multilingual_audit)
print("Forrásonkénti QA összesítés (egyedi cikkek; nem RSS-megjelenések):", source_totals)
for item in per_source:
    if item["short_text"] or item["quote_mismatch"] or item["numeric_evidence"]:
        print("Forrás QA:", {
            "source_id": item["source_id"], "source": item["source"], "country": item["country"],
            "short_text": item["short_text"],
            "short_text_retried": item["short_text_retried"],
            "recent_short_text": item["recent_short_text"],
            "quote_mismatch": item["quote_mismatch"],
            "recent_quote_mismatch": item["recent_quote_mismatch"],
            "numeric_evidence": item["numeric_evidence"],
        })

# Safe aggregate-only details from the newest run help separate genuinely
# eligible news from old entries and a queue exhausted during preflight.
import json
run_path = db_path.parent / "last_run.json"
if run_path.exists():
    report = json.loads(run_path.read_text(encoding="utf-8"))
    for key in ("intake", "pending_before_ai", "capacity", "ai", "translations"):
        if key in report:
            print(f"{key}:", json.dumps(report[key], ensure_ascii=False))

