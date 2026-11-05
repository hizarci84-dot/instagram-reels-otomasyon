@echo off
chcp 65001 > nul
title Hemen Siradaki Reels Videosunu Paylas
cd /d "%~dp0"
echo ====================================================================
echo  GitHub ile senkronize ediliyor...
echo ====================================================================
git pull --rebase origin main
echo.
python upload_reels.py --force
echo.
git add yuklenenler.json
git commit -m "Manuel Reels Paylasimi"
git push origin main
pause
