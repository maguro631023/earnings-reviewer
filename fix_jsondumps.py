#!/usr/bin/env python3
"""fix_jsondumps.py — 移除 json.dumps() 裡誤加的 encoding 參數"""
import re
from pathlib import Path

for py_file in sorted(Path("src").rglob("*.py")):
    original = py_file.read_text(encoding="utf-8")
    # 移除 json.dumps(..., encoding="utf-8") 裡的 encoding 參數
    patched = re.sub(r',\s*encoding=["\']utf-8["\'](\s*\))', r'\1', original)
    if patched != original:
        py_file.write_text(patched, encoding="utf-8")
        print(f"  fixed: {py_file}")

print("\ndone. now run:")
print("  python src/rules_engine/engine.py --ticker NVDA --period Q1_2026 --sector semis")
print("  python src/model/model_updater.py --ticker NVDA --period Q1_2026")
print("  python src/report/generator.py    --ticker NVDA --period Q1_2026")
