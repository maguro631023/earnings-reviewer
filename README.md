# 📊 Earnings Reviewer — Expert System

AI 驅動的法說會與財報專家系統。自動擷取投資訊號、更新財務模型假設，標記投資論點重大變化。

## 快速開始

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."

# 將逐字稿 PDF 或 TXT 放入 data/raw/
python src/ingest/loader.py       --ticker NVDA --period Q1_2026
python src/extract/extractor.py   --ticker NVDA --period Q1_2026
python src/rules_engine/engine.py --ticker NVDA --period Q1_2026 --sector semis
python src/model/model_updater.py --ticker NVDA --period Q1_2026
python src/report/generator.py    --ticker NVDA --period Q1_2026
# → 開啟 docs/index.html 檢視 Dashboard
```

## 部署至 GitHub Pages

```bash
git init && git add . && git commit -m "feat: Earnings Reviewer v1"
gh repo create earnings-reviewer --public --push --source=.
gh secret set OPENAI_API_KEY --body "sk-..."
# GitHub → Settings → Pages → Branch: main / docs
```

## 觸發 GitHub Actions 分析管線

```bash
# 手動觸發
gh workflow run analyze.yml -f ticker=NVDA -f period=Q1_2026 -f sector=semis

# 或 push 財報檔自動觸發
cp transcript.pdf data/raw/NVDA_Q1_2026_transcript.pdf
git add data/raw/ && git commit -m "add NVDA Q1 2026" && git push
```

## 自訂規則庫

編輯 `rules/general.yaml` 或新增 `rules/sector_XXX.yaml`。
- severity: `critical` | `warning` | `info`
- action:   `thesis_break` | `revise_assumption` | `monitor` | `acknowledge`

## 專案結構

```
earnings-reviewer/
├─ docs/
│  ├─ index.html          # GitHub Pages Dashboard (上傳 JSON 或拖放)
│  └─ data/latest.json    # Actions 自動更新
├─ src/
│  ├─ ingest/loader.py    # PDF/TXT → chunked JSON
│  ├─ extract/extractor.py# GPT-4o 訊號抽取
│  ├─ rules_engine/engine.py # YAML 規則評估引擎
│  ├─ model/model_updater.py # 財務模型假設更新
│  └─ report/generator.py   # 合併報告 + 發布 latest.json
├─ rules/
│  ├─ general.yaml        # 通用規則 10 條
│  └─ sector_semis.yaml   # 半導體規則 6 條
├─ data/raw/              # 放入法說會逐字稿 / 財報 PDF
├─ reports/               # 分析輸出
├─ .github/workflows/analyze.yml
└─ requirements.txt
```

## License
MIT
"# earnings-reviewer" 
