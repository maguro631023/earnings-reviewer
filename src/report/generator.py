import click, json
from pathlib import Path
from datetime import datetime, timezone

REPORTS_DIR = Path("reports")
DOCS_DATA   = Path("docs/data")

def determine_status(findings):
    crits = [f for f in findings if f["severity"] == "critical"]
    warns = [f for f in findings if f["severity"] == "warning"]
    if any(f["action"] == "thesis_break" for f in crits):
        return "break"
    if crits or len(warns) >= 3:
        return "watch"
    return "intact"

@click.command()
@click.option("--ticker", default="AUTO")
@click.option("--period", default="LATEST")
def main(ticker, period):
    ff = REPORTS_DIR / f"{ticker}_{period}_findings.json"
    mf = REPORTS_DIR / f"{ticker}_{period}_model_updates.json"

    fd = json.loads(ff.read_text(encoding="utf-8")) if ff.exists() else {}
    md = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}

    findings = fd.get("findings", [])
    status   = determine_status(findings)
    crits    = [f for f in findings if f["severity"] == "critical"]
    warns    = [f for f in findings if f["severity"] == "warning"]

    report = {
        "meta": {
            "ticker": ticker,
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "thesis_status": status,
        },
        "summary": {
            "critical_count": len(crits),
            "warning_count": len(warns),
            "model_updates_count": len(md.get("updates", [])),
            "thesis_status": status,
        },
        "findings": findings,
        "model_updates": md.get("updates", []),
        "key_quotes": fd.get("signals", {}).get("key_quotes", []),
        "signals": fd.get("signals", {}),
    }

    out = REPORTS_DIR / f"{ticker}_{period}_report.json"
    out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    (DOCS_DATA / "latest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    s = report["summary"]
    icon = {"intact": "OK", "watch": "WATCH", "break": "BREAK"}.get(s["thesis_status"], "?")
    click.echo("[report] Thesis: " + icon + " / " + s["thesis_status"].upper())
    click.echo(
        "[report] Critical: " + str(s["critical_count"]) +
        "  Warnings: " + str(s["warning_count"]) +
        "  Model updates: " + str(s["model_updates_count"])
    )
    click.echo("[report] Saved: " + str(out))
    click.echo("[report] Saved: docs/data/latest.json")

if __name__ == "__main__":
    main()