@echo off
chcp 65001 > nul
title Instagram Token Kopyala (GitHub Secrets Icin)
cd /d "%~dp0"
if not exist "ig_token.json" (
    echo [HATA] ig_token.json bulunamadi! Lutfen once giris_yap.bat calistirin.
    pause
    exit /b 1
)
python -c "import json, subprocess; data=json.load(open('ig_token.json', encoding='utf-8')); p=subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True); p.communicate(json.dumps(data, ensure_ascii=False).encode('utf-8')); print('\n[OK] ig_token.json icerigi panoya kopyalandi! GitHub -> Settings -> Secrets -> Actions -> IG_TOKEN_JSON icine Ctrl+V ile yapistirabilirsiniz.\n')"
pause
