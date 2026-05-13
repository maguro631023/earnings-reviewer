"""extractor.py — GPT-4o signal extraction from transcript chunks
Usage: python src/extract/extractor.py --ticker AAPL --period Q1_2026
"""
import click, json, os
from pathlib import Path

try:
    from openai import OpenAI
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
except ImportError:
    _client = None

DATA_PROC = Path("data/processed")

SCHEMA = """{
  "revenue_guidance_delta_pct": <float|null>,
  "gross_margin_delta_bps": <float|null>,
  "dio_delta_days": <float|null>,
  "management_demand_narrative": [<keywords>],
  "management_tone": <"bullish"|"neutral"|"cautious"|"negative">,
  "management_tone_delta": <float -1 to 1|null>,
  "new_risk_factors_count": <int>,
  "fcf_vs_model_pct": <float|null>,
  "buyback_status_change": <"intact"|"reduced"|"suspended"|null>,
  "book_to_bill": <float|null>,
  "datacenter_revenue_growth_pct": <float|null>,
  "china_revenue_pct": <float|null>,
  "fab_utilization_pct": <float|null>,
  "top1_customer_revenue_pct": <float|null>,
  "lead_time_delta_weeks": <float|null>,
  "key_quotes": [<up to 3 verbatim high-importance quotes>],
  "thesis_change_signals": [<description strings>],
  "model_assumption_updates": [
    {"driver":<str>,"from":<str>,"to":<str>,"confidence":<"high"|"medium"|"low">}
  ]
}"""

PROMPT = ("You are a senior equity analyst. Extract signals from this earnings call excerpt.\n"
          "Return ONLY valid JSON matching this schema:\n" + SCHEMA +
          "\nTranscript excerpt:\n\"\"\"\n{chunk}\n\"\"\"")

def extract_chunk(text):
    if not _client:
        return {"error": "OpenAI client unavailable — set OPENAI_API_KEY"}
    try:
        r = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Financial analyst. Return only valid JSON."},
                {"role": "user",   "content": PROMPT.format(chunk=text[:3000])},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(r.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def merge(signals_list):
    merged = {}
    for s in signals_list:
        for k, v in s.items():
            if v is None or k == "error": continue
            if k not in merged:
                merged[k] = v
            elif isinstance(v, list):
                merged[k] = merged.get(k, []) + v
            elif isinstance(v, (int, float)) and isinstance(merged.get(k), (int, float)):
                merged[k] = round((merged[k] + v) / 2, 4)
    return merged

@click.command()
@click.option("--ticker",      default="AUTO")
@click.option("--period",      default="LATEST")
@click.option("--max-chunks",  default=20)
def main(ticker, period, max_chunks):
    f = DATA_PROC / f"{ticker}_{period}_chunks.json"
    if not f.exists():
        click.echo(f"[extractor] ❌ Not found: {f}"); return
    docs = json.loads(f.read_text()); sigs = []
    for doc in docs:
        chunks = doc["chunks"][:max_chunks]
        for i, c in enumerate(chunks):
            click.echo(f"[extractor] {doc['file']} chunk {i+1}/{len(chunks)}")
            sigs.append(extract_chunk(c))
    merged = merge(sigs)
    merged["ticker"] = ticker; merged["period"] = period
    out = DATA_PROC / f"{ticker}_{period}_signals.json"
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    click.echo(f"[extractor] ✅ Saved → {out}")

if __name__ == "__main__": main()
