@echo off
chcp 65001 > nul
echo Fixing encoding...
python fix_encoding.py
pause
