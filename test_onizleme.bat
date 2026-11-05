@echo off
chcp 65001 > nul
title Siradaki Reels Onizleme (Test Modu)
cd /d "%~dp0"
python upload_reels.py --dry-run
pause
