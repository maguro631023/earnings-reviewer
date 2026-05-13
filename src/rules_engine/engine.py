"""engine.py — Expert system YAML rules evaluator
Usage: python src/rules_engine/engine.py --ticker AAPL --period Q1_2026 --sector general
"""
import click, json, yaml
from pathlib import Path

DATA_PROC  = Path("data/processed")
RULES_DIR  = Path("rules")
REPORTS_DIR= Path("reports")

def load_rules(sector="general"):
    rules = []
    for f in sorted(RULES_DIR.glob("*.yaml")):
        d = yaml.safe_load(f.read_text())
        if d.get("sector") in ("general", sector):
            rules.extend(d.get("rules", []))
    return rules

def eval_cond(cond, sigs):
    if "combined" in cond:
        return all(eval_cond(c, sigs)[0] for c in cond["combined"]), None
    v = sigs.get(cond.get("field"))
    if v is None: return False, None
    op  = cond.get("operator")
    thr = cond.get("threshold")
    contains = cond.get("contains", [])
    eq  = cond.get("value")
    if op == "less_than":
        try:    return float(v) < thr, v
        except: return False, v
    elif op == "greater_than":
        try:    return float(v) > thr, v
        except: return False, v
    elif op == "equals":
        return str(v) == str(eq), v
    elif contains:
        hay = " ".join(v).lower() if isinstance(v, list) else str(v).lower()
        return any(k.lower() in hay for k in contains), v
    return False, v

def fmt_msg(msg, val, thr):
    try:    msg = msg.replace("{value}", str(round(float(val), 2)) if val is not None else "N/A")
    except: msg = msg.replace("{value}", str(val) if val else "N/A")
    return msg.replace("{threshold}", str(thr) if thr is not None else "")

@click.command()
@click.option("--ticker", default="AUTO")
@click.option("--period", default="LATEST")
@click.option("--sector", default="general")
def main(ticker, period, sector):
    sf = DATA_PROC / f"{ticker}_{period}_signals.json"
    if not sf.exists():
        click.echo(f"[engine] ❌ Not found: {sf}"); return
    sigs = json.loads(sf.read_text())
    findings = []
    for rule in load_rules(sector):
        ok, val = eval_cond(rule["condition"], sigs)
        if ok:
            findings.append({
                "rule_id":  rule["id"],
                "name":     rule["name"],
                "severity": rule["severity"],
                "action":   rule["action"],
                "message":  fmt_msg(rule["message"], val, rule["condition"].get("threshold")),
                "tags":     rule.get("tags", []),
            })
    findings.sort(key=lambda x: {"critical":0,"warning":1,"info":2}[x["severity"]])
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{ticker}_{period}_findings.json"
    out.write_text(json.dumps(
        {"ticker":ticker,"period":period,"findings":findings,"signals":sigs},
        indent=2, ensure_ascii=False))
    icons = {"critical":"🔴","warning":"🟡","info":"🔵"}
    click.echo(f"\n[engine] {len(findings)} rules triggered:")
    for f in findings:
        click.echo(f"  {icons[f['severity']]} [{f['rule_id']}] {f['message']}")
    click.echo(f"\n[engine] ✅ Saved → {out}")

if __name__ == "__main__": main()
