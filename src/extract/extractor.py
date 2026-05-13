"""extractor.py — GPT-4o signal extractor
Usage: python src/extract/extractor.py --ticker NVDA --period Q1_2026
"""
import click, json, os
from pathlib import Path

DATA_PROC = Path("data/processed")

SYSTEM_PROMPT = """You are a senior equity analyst. Extract structured financial signals from earnings call transcripts and press releases.

Return ONLY valid JSON with these exact fields (use null if not available):
{
  "revenue_actual":              <float, in billions USD or null>,
  "revenue_guidance_next_q":     <float, in billions USD or null>,
  "revenue_guidance_delta_pct":  <float, % change vs prior guidance or null>,
  "gross_margin_actual_pct":     <float, actual GM% or null>,
  "gross_margin_guidance_pct":   <float, guided GM% or null>,
  "gross_margin_delta_bps":      <float, bps change vs prior quarter or null>,
  "fcf_vs_model_pct":            <float, FCF beat/miss % vs estimate or null>,
  "inventory_days_delta":        <float, change in inventory days or null>,
  "management_tone_score":       <float, -1.0 to +1.0, negative=cautious, positive=confident>,
  "china_revenue_pct":           <float, % of revenue from China or null>,
  "capex_guidance_bn":           <float, capex guidance in billions or null>,
  "narrative_flags":             <list of strings: observed risk/opportunity flags>,
  "key_quotes":                  <list of 3-5 most important management quotes>,
  "model_assumption_updates":    <list of {driver, from, to, confidence} objects>,
  "thesis_signals": {
    "bull_case_intact":  <bool>,
    "bear_case_risk":    <bool>,
    "new_risk_factors":  <list of strings>
  }
}"""

def extract_signals(chunks: list[dict]) -> dict:
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit("pip install openai")

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    combined = {}

    for chunk in chunks:
        text = chunk.get("text", "")[:6000]
        resp = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Document: {chunk.get('source','unknown')}\n\n{text}"},
            ]
        )
        try:
            parsed = json.loads(resp.choices[0].message.content)
        except Exception:
            continue

        # merge: keep non-null values, extend lists
        for k, v in parsed.items():
            if v is None:
                continue
            if isinstance(v, list) and k in combined and isinstance(combined[k], list):
                combined[k] = list({str(x): x for x in combined[k] + v}.values())
            elif isinstance(v, dict) and k in combined and isinstance(combined[k], dict):
                combined[k].update({kk: vv for kk, vv in v.items() if vv is not None})
            elif k not in combined:
                combined[k] = v
        click.echo(f"[extractor] {chunk.get('source','?')} chunk {chunk.get('chunk_index','?')+1}/{chunk.get('total_chunks','?')} ✅")

    return combined

@click.command()
@click.option("--ticker", default="AUTO")
@click.option("--period", default="LATEST")
def main(ticker, period):
    cf = DATA_PROC / f"{ticker}_{period}_chunks.json"
    if not cf.exists():
        click.echo(f"[extractor] Not found: {cf}"); return
    chunks = json.loads(cf.read_text(encoding="utf-8"))

    signals = extract_signals(chunks)
    signals["ticker"] = ticker
    signals["period"] = period

    out = DATA_PROC / f"{ticker}_{period}_signals.json"
    out.write_text(json.dumps(signals, indent=2, ensure_ascii=False, encoding="utf-8"), encoding="utf-8")

    click.echo(f"\n[extractor] Extracted {len(signals)} signal fields")
    click.echo(f"[extractor] ✅ Saved → {out}")

    # show key fields
    for key in ["revenue_actual","revenue_guidance_next_q","gross_margin_actual_pct",
                "gross_margin_delta_bps","management_tone_score","china_revenue_pct"]:
        click.echo(f"  {key}: {signals.get(key)}")

if __name__ == "__main__": main()
