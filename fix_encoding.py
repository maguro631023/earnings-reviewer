#!/usr/bin/env python3
"""
fix_encoding.py — 修復所有 .py 檔案的 cp950 encoding 問題
在 earnings-reviewer 根目錄執行：python fix_encoding.py
"""
import re
from pathlib import Path

src_dir = Path("src")
fixed_files = []

for py_file in src_dir.rglob("*.py"):
    original = py_file.read_text(encoding="utf-8")
    patched  = original

    # read_text() → read_text(encoding="utf-8")
    patched = re.sub(
        r'\.read_text\(\)',
        '.read_text(encoding="utf-8")',
        patched
    )
    # write_text(... ) — 只在沒有 encoding 參數時補上
    patched = re.sub(
        r'\.write_text\(([^)]+)\)',
        lambda m: m.group(0) if 'encoding' in m.group(1)
                  else f'.write_text({m.group(1)}, encoding="utf-8")',
        patched
    )
    # datetime.utcnow() deprecation fix
    patched = patched.replace(
        "from datetime import datetime",
        "from datetime import datetime, timezone"
    )
    patched = patched.replace(
        "datetime.utcnow().isoformat() + \"Z\"",
        "datetime.now(timezone.utc).isoformat().replace(\'+00:00\', \'Z\')"
    )

    if patched != original:
        py_file.write_text(patched, encoding="utf-8")
        fixed_files.append(str(py_file))
        print(f"  ✅ Fixed: {py_file}")

if not fixed_files:
    print("  ℹ️  所有檔案已是正確 encoding，無需修復")
else:
    print(f"\n✅ 共修復 {len(fixed_files)} 個檔案")

print("\n請重新執行：")
print("  python src/rules_engine/engine.py  --ticker NVDA --period Q1_2026 --sector semis")
print("  python src/model/model_updater.py  --ticker NVDA --period Q1_2026")
print("  python src/report/generator.py     --ticker NVDA --period Q1_2026")
