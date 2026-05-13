"""engine.py — Expert system YAML rules evaluator
Usage: python src/rules_engine/engine.py --ticker NVDA --period Q1_2026 --sector semis
"""
import click, json, yaml
from pathlib import Path

DATA_PROC   = Path("data/processed")
RULES_DIR   = Path("rules")
REPORTS_DIR = Path("reports")

def load_rules(sector="general"):
    rules = []
    for f in sorted(RULES_DIR.glob("*.yaml")):
        # ★ 修復：明確指定 utf-8 讀取
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if d.get("sector") in ("general", sector):
            rules.extend(d.get("rules", []))
    return rules

def eval_cond(cond, sigs):
    if "combined" in cond:
        return all(eval_cond(c, sigs)[0] for c in cond["combined"]), None
    field    = cond.get("field")
    v        = sigs.get(field)
    op       = cond.get("operator")
    thr      = cond.get("threshold")
    contains = cond.get("contains", [])
    eq       = cond.get("value")

    if v is None:
        return False, None

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

    # boolean field (e.g. flag fields)
    if isinstance(v, bool):
        return v is True, v

    return False, v

def fmt_msg(msg, val, thr):
    try:    msg = msg.replace("{value}", str(round(float(val), 2)) if val is not None else "N/A")
    except: msg = msg.replace("{value}", str(val) if val else "N/A")
    return msg.replace("{threshold}", str(thr) if thr is not None else "")

@click.command()
@click.option("--ticker",  default="AUTO")
@click.option("--period",  default="LATEST")
@click.option("--sector",  default="general")
def main(ticker, period, sector):
    sf = DATA_PROC / f"{ticker}_{period}_signals.json"
    if not sf.exists():
        click.echo(f"[engine] Not found: {sf}"); return
    sigs = json.loads(sf.read_text(encoding="utf-8"))

    # ★ 展平巢狀結構方便規則比對
    flat = dict(sigs)
    # 從 guidance 子物件提取
    for k, v in (sigs.get("guidance") or {}).items():
        flat.setdefault(f"guidance_{k}", v)
    # 從 metrics 提取
    for k, v in (sigs.get("metrics") or {}).items():
        flat.setdefault(k, v)
    for k, v in (sigs.get("key_metrics") or {}).items():
        flat.setdefault(k, v)
    # narrative flags → list
    if "narrative_flags" in sigs and isinstance(sigs["narrative_flags"], list):
        flat["narrative_flags"] = sigs["narrative_flags"]
    if "risk_flags" in sigs and isinstance(sigs["risk_flags"], list):
        flat["risk_flags"] = sigs["risk_flags"]
    # 自動從 sentiment 抽 score
    sent = sigs.get("sentiment") or sigs.get("management_tone") or {}
    if isinstance(sent, dict):
        flat.setdefault("management_tone_score", sent.get("score", sent.get("tone_score")))
    elif isinstance(sent, (int, float)):
        flat.setdefault("management_tone_score", sent)

    findings = []
    for rule in load_rules(sector):
        ok, val = eval_cond(rule["condition"], flat)
        if ok:
            findings.append({
                "rule_id":  rule["id"],
                "name":     rule["name"],
                "severity": rule["severity"],
                "action":   rule["action"],
                "message":  fmt_msg(rule["message"], val,
                                    rule["condition"].get("threshold")),
                "tags":     rule.get("tags", []),
            })

    findings.sort(key=lambda x: {"critical":0,"warning":1,"info":2}[x["severity"]])
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{ticker}_{period}_findings.json"
    out.write_text(json.dumps(
        {"ticker": ticker, "period": period,
         "findings": findings, "signals": sigs},
        indent=2, ensure_ascii=False), encoding="utf-8")

    icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    click.echo(f"\n[engine] {len(findings)} rules triggered:")
    for f in findings:
        click.echo(f"  {icons[f['severity']]} [{f['rule_id']}] {f['message']}")
    click.echo(f"\n[engine] Saved → {out}")

if __name__ == "__main__": main()
