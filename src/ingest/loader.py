"""loader.py — PDF/TXT ingestion to chunked JSON
Usage: python src/ingest/loader.py --ticker AAPL --period Q1_2026
"""
import click, json, re
from pathlib import Path
try:
    import pdfplumber; HAS_PDF = True
except ImportError:
    HAS_PDF = False

DATA_RAW  = Path("data/raw")
DATA_PROC = Path("data/processed")

def load_pdf(p):
    if not HAS_PDF: raise RuntimeError("pip install pdfplumber")
    with pdfplumber.open(p) as pdf:
        return "\n".join(pg.extract_text() or "" for pg in pdf.pages)

def load_text(p): return p.read_text(encoding="utf-8", errors="ignore")

def clean(t):
    t = re.sub(r"\s+", " ", t)
    return re.sub(r"[^\x00-\x7F]", " ", t).strip()

def chunk(t, size=1500, overlap=200):
    w = t.split(); out = []; i = 0
    while i < len(w):
        out.append(" ".join(w[i:i+size])); i += size - overlap
    return out

@click.command()
@click.option("--ticker",      default="AUTO")
@click.option("--period",      default="LATEST")
@click.option("--input","inp", default=None)
@click.option("--chunk-size",  default=1500)
def main(ticker, period, inp, chunk_size):
    DATA_PROC.mkdir(parents=True, exist_ok=True)
    files = [Path(inp)] if inp else             sorted(DATA_RAW.glob("*.pdf")) + sorted(DATA_RAW.glob("*.txt"))
    if not files:
        click.echo("[loader] ⚠️  No files in data/raw/ — add a PDF or TXT first."); return
    result = []
    for f in files:
        click.echo(f"[loader] Processing {f.name}")
        try:
            raw = load_pdf(f) if f.suffix.lower() == ".pdf" else load_text(f)
        except Exception as e:
            click.echo(f"[loader] ❌ {e}"); continue
        t = clean(raw); c = chunk(t, chunk_size)
        result.append({"file": f.name, "chunks": c,
                        "total_chunks": len(c), "char_count": len(t)})
        click.echo(f"[loader]   → {len(c)} chunks, {len(t):,} chars")
    out = DATA_PROC / f"{ticker}_{period}_chunks.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    click.echo(f"[loader] ✅ Saved → {out}")

if __name__ == "__main__": main()
