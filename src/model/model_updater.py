import click, json
from pathlib import Path

DATA_PROC   = Path("data/processed")
REPORTS_DIR = Path("reports")

DEFAULT_MODEL = {
    "revenue_growth_pct": 15.0, "gross_margin_pct": 43.0,
    "opex_growth_pct": 8.0, "capex_pct_revenue": 5.0,
    "fcf_margin_pct": 22.0, "ev_ebitda_multiple": 18.0,
}
SENSITIVITY = {
    "revenue_guidance_delta_pct": {"driver":"revenue_growth_pct","mult":1.0,"note":"Guidance revision"},
    "gross_margin_delta_bps":     {"driver":"gross_margin_pct","mult":0.01,"note":"GM delta (bps)"},
    "fcf_vs_model_pct":           {"driver":"fcf_margin_pct","mult":0.1,"note":"FCF miss/beat"},
}

@click.command()
@click.option("--ticker", default="AUTO")
@click.option("--period", default="LATEST")
def main(ticker, period):
    sf = DATA_PROC / f"{ticker}_{period}_signals.json"
    if not sf.exists():
        click.echo(f"[model] Not found: {sf}"); return
    sigs = json.loads(sf.read_text(encoding="utf-8"))
    base = DEFAULT_MODEL.copy()
    updates = []
    for sig, m in SENSITIVITY.items():
        delta = sigs.get(sig)
        if delta is None: continue
        old = base.get(m["driver"], 0.0)
        chg = round(float(delta) * m["mult"], 2)
        updates.append({"driver":m["driver"],"from":old,"to":round(old+chg,2),"change":chg,"source_signal":sig,"note":m["note"]})
    for u in sigs.get("model_assumption_updates", []):
        updates.append({"driver":u.get("driver"),"from":u.get("from"),"to":u.get("to"),
                        "confidence":u.get("confidence"),"source_signal":"llm_extracted",
                        "note":"Extracted from transcript"})
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{ticker}_{period}_model_updates.json"
    out.write_text(
        json.dumps({"ticker":ticker,"period":period,"base_model":DEFAULT_MODEL,"updates":updates},
                   indent=2, ensure_ascii=False),
        encoding="utf-8")
    click.echo(f"\n[model] {len(updates)} assumption updates:")
    for u in updates:
        click.echo(f"  📐 {u['driver']}: {u['from']} → {u['to']}  ({u['note']})")
    click.echo(f"\n[model] ✅ Saved → {out}")

if __name__ == "__main__": main()
