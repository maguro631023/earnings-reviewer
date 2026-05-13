"""generator.py — Report builder + GitHub Pages data publisher
Usage: python src/report/generator.py --ticker AAPL --period Q1_2026
"""
import click, json
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path("reports")
DOCS_DATA   = Path("docs/data")

def determine_status(findings):
    crits = [f for f in findings if f["severity"] == "critical"]
    warns = [f for f in findings if f["severity"] == "warning"]
    if any(f["action"] == "thesis_break" for f in crits): return "break"
    if crits or len(warns) >= 3: return "watch"
    return "intact"

def build_report(ticker, period, fd, md):
    findings = fd.get("findings", [])
    status   = determine_status(findings)
    crits    = [f for f in findings if f["severity"] == "critical"]
    warns    = [f for f in findings if f["severity"] == "warning"]
    return {
        "meta": {
            "ticker": ticker, "period": period,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "thesis_status": status,
        },
        "summary": {
            "critical_count":      len(crits),
            "warning_count":       len(warns),
            "model_updates_count": len(md.get("updates", [])),
            "thesis_status":       status,
        },
        "findings":      findings,
        "model_updates": md.get("updates", []),
        "key_quotes":    fd.get("signals", {}).get("key_quotes", []),
        "signals":       fd.get("signals", {}),
    }

@click.command()
@click.option("--ticker", default="AUTO")
@click.option("--period", default="LATEST")
def main(ticker, period):
    ff = REPORTS_DIR / f"{ticker}_{period}_findings.json"
    mf = REPORTS_DIR / f"{ticker}_{period}_model_updates.json"
    fd = json.loads(ff.read_text()) if ff.exists() else {}
    md = json.loads(mf.read_text()) if mf.exists() else {}
    report = build_report(ticker, period, fd, md)
    out = REPORTS_DIR / f"{ticker}_{period}_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    (DOCS_DATA / "latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    s = report["summary"]
    icons = {"intact":"✅","watch":"⚠️","break":"🔴"}
    click.echo(f"\n[report] {icons.get(s['thesis_status'],'❓')} Thesis: {s['thesis_status'].upper()}")
    click.echo(f"[report] Critical: {s['critical_count']}  Warnings: {s['warning_count']}  Model updates: {s['model_updates_count']}")
    click.echo(f"[report] ✅ {out}")
    click.echo(f"[report] ✅ docs/data/latest.json")

if __name__ == "__main__": main()
