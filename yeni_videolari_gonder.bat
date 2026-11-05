@echo off
chcp 65001 > nul
title Yeni Wox Reels Videolarini GitHub'a Gonder
cd /d "%~dp0"
echo ====================================================================
echo  Masaustundeki 'Wox Tarzi Reels (9x16)' klasoru taranip esitleniyor...
echo ====================================================================
python -c "import os, shutil; src=r'C:\Users\hizar\OneDrive\Desktop\Wox Tarzı Reels (9x16)'; dst='REELS_VIDEOLARI'; skip={'bolunebilme_3_9_neural.mp4','dogum_gunu_paradoksu_final.mp4','thales_teoremi_final.mp4','pascal_fraktal_final.mp4','final_ders_videosu.mp4'}; os.makedirs(dst, exist_ok=True); added=[shutil.copy2(os.path.join(src,f), os.path.join(dst,f)) or f for f in os.listdir(src) if f.endswith('.mp4') and f not in skip and not os.path.exists(os.path.join(dst,f))]; print(f'Yeni eklenen video sayisi: {len(added)}', added)"
git pull --rebase origin main
git add REELS_VIDEOLARI reels_katalogu.json yuklenenler.json
git commit -m "Yeni Reels videolari eklendi"
git push origin main
echo.
echo [TAMAMLANDI] Yeni videolar basariyla GitHub bulut sistemine gonderildi!
pause
