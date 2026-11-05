# -*- coding: utf-8 -*-
"""
Instagram Graph API Kurulum ve Token Sihirbazı (@mufithocailematematik)
Bu betik:
1. Girdiğiniz Meta Access Token ile @mufithocailematematik hesabınızın IG_USER_ID numarasını otomatik bulur.
2. İsterseniz App ID ve App Secret ile kısa süreli token'ı 60 günlük / süresiz uzun ömürlü token'a dönüştürür.
3. Antalya konum ID'sini doğrular ve ig_token.json dosyasını oluşturup panoya (Ctrl+V) kopyalar.
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.parse
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
TOKEN_FILE = "ig_token.json"
DEFAULT_ANTALYA_LOCATION_ID = "106078429431815"


def api_get(endpoint: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{GRAPH_BASE_URL}/{endpoint.lstrip('/')}?{query}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def copy_to_clipboard(text: str) -> bool:
    try:
        p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        p.communicate(input=text.encode("utf-8"))
        return p.returncode == 0
    except Exception:
        return False


def main():
    print("=" * 72)
    print(" INSTAGRAM REELS OTOMASYONU - META GRAPH API KURULUM SİHİRBAZI")
    print(" Hesap: @mufithocailematematik")
    print("=" * 72)
    print("\nAdım 1: https://developers.facebook.com/tools/explorer/ adresini açın.")
    print("Adım 2: Sağdaki 'Permissions' kısmından şu izinleri ekleyin:")
    print("        - instagram_basic")
    print("        - instagram_content_publish")
    print("        - pages_show_list")
    print("        - pages_read_engagement")
    print("Adım 3: 'Generate Access Token' butonuna tıklayıp oluşan kodu aşağıya yapıştırın.\n")

    raw_token = input("Meta Access Token yapıştırın: ").strip()
    if not raw_token:
        print("Hata: Token boş bırakılamaz.")
        sys.exit(1)

    print("\n[İsteğe Bağlı] Token'ı 60 günlük / uzun ömürlü yapmak için Meta App bilgilerinizi")
    print("girebilirsiniz (Boş geçmek için doğrudan Enter'a basın):")
    app_id = input("Meta App ID (Enter = Atla): ").strip()
    app_secret = input("Meta App Secret (Enter = Atla): ").strip() if app_id else ""

    access_token = raw_token
    if app_id and app_secret:
        try:
            print("-> Uzun ömürlü (Long-Lived) Token alınıyor...")
            ex_res = api_get("oauth/access_token", {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": raw_token,
            })
            if ex_res.get("access_token"):
                access_token = ex_res["access_token"]
                print("   + Uzun ömürlü Token başarıyla alındı!")
        except Exception as e:
            print(f"   ! Uzun ömürlü token dönüşümü atlandı ({e}), mevcut token kullanılacak.")

    # Instagram Business / Creator ID'sini otomatik bul
    ig_user_id = None
    ig_username = "mufithocailematematik"
    print("\n-> Bağlı Instagram Profesyonel Hesabı (@mufithocailematematik) aranıyor...")
    try:
        accounts_res = api_get("me/accounts", {
            "fields": "id,name,access_token,instagram_business_account{id,username,name}",
            "access_token": access_token,
        })
        pages = accounts_res.get("data", [])
        for page in pages:
            ig_acc = page.get("instagram_business_account")
            if ig_acc and ig_acc.get("id"):
                ig_user_id = str(ig_acc["id"])
                ig_username = ig_acc.get("username", ig_username)
                print(f"   + Bulundu! Sayfa: {page.get('name')} -> Instagram: @{ig_username} (ID: {ig_user_id})")
                if ig_username.lower() == "mufithocailematematik":
                    break
    except Exception as e:
        print(f"   ! Otomatik sayfa taraması bilgi mesajı: {e}")

    if not ig_user_id:
        print("\nInstagram Hesap ID'si (IG_USER_ID) otomatik listelenemedi.")
        ig_user_id = input("Lütfen Instagram Business/Creator Hesap ID'nizi girin (Örn: 178414...): ").strip()
        if not ig_user_id:
            print("Hata: Instagram Hesap ID'si gereklidir.")
            sys.exit(1)

    # Antalya konum ID'sini kontrol et
    location_id = DEFAULT_ANTALYA_LOCATION_ID
    try:
        loc_res = api_get("pages/search", {
            "q": "Antalya",
            "fields": "id,name,location",
            "access_token": access_token,
        })
        for item in loc_res.get("data", []):
            if "antalya" in item.get("name", "").lower():
                location_id = str(item["id"])
                print(f"   + Antalya Konum ID doğrulandı: {location_id} ({item.get('name')})")
                break
    except Exception:
        print(f"   + Varsayılan Antalya Konum ID ayarlandı: {location_id}")

    token_payload = {
        "username": ig_username,
        "ig_user_id": ig_user_id,
        "access_token": access_token,
        "location_name": "Antalya",
        "location_id": location_id,
        "app_id": app_id,
        "app_secret": app_secret,
        "github_repo": "hizarci84-dot/instagram-reels-otomasyon",
    }

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_payload, f, indent=2, ensure_ascii=False)

    compact_json = json.dumps(token_payload, ensure_ascii=False)
    copied = copy_to_clipboard(compact_json)

    print("\n" + "=" * 72)
    print(f" ✅ KURULUM TAMAMLANDI! '{TOKEN_FILE}' dosyası kaydedildi.")
    if copied:
        print(" 📋 Token JSON verisi otomatik olarak PANOYA KOPYALANDI (Ctrl+V ile yapıştırabilirsiniz)!")
    print("\n GitHub Actions Bulut Otomasyonu İçin Son Adım:")
    print(" 1. GitHub deponuzda: Settings -> Secrets and variables -> Actions sayfasına gidin.")
    print(" 2. 'New repository secret' butonuna tıklayın.")
    print(" 3. Name kısmına: IG_TOKEN_JSON yazın.")
    print(" 4. Secret kısmına: Ctrl+V yaparak panodaki veriyi yapıştırın ve 'Add secret' deyin.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
