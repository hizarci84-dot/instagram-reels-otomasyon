# -*- coding: utf-8 -*-
"""
Instagram Reels Günlük Otomatik Paylaşım Sistemi (@mufithocailematematik)
Resmi Meta / Instagram Graph API kullanarak her gün saat 18:00'de
sıradaki Wox tarzı 9:16 matematik animasyonunu otomatik açıklama ve
Antalya konumuyla Reels olarak paylaşır.
"""

import os
import sys
import json
import re
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Türkiye Saati (UTC+3)
TRT_TZ = timezone(timedelta(hours=3))

VIDEOS_DIR = "REELS_VIDEOLARI"
CATALOG_FILE = "reels_katalogu.json"
TRACKER_FILE_DEFAULT = "yuklenenler.json"
TOKEN_FILE_DEFAULT = "ig_token.json"
GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
RUPLOAD_BASE_URL = f"https://rupload.facebook.com/ig-api-upload/{GRAPH_API_VERSION}"

# Antalya Resmi Facebook/Instagram Konum Sayfası ID'si (Yedekli)
DEFAULT_ANTALYA_LOCATION_ID = "106078429431815"


def now_trt() -> datetime:
    """Türkiye saatine (UTC+3) göre şu anki zamanı döndürür."""
    return datetime.now(TRT_TZ)


def clean_video_title_from_filename(filename: str) -> str:
    """Katalogda olmayan yeni bir video eklendiğinde dosya adından temiz başlık üretir."""
    name, _ = os.path.splitext(filename)
    clean = re.sub(r"^\d+[\s\-_.]*", "", name)
    clean = re.sub(r"_final(_raw)?$", "", clean, flags=re.IGNORECASE)
    clean = clean.replace("_", " ").strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean.title()


def build_fallback_metadata(filename: str) -> dict:
    """Katalogda tanımlı olmayan yeni videolar için otomatik açıklama ve soru üretir."""
    clean_title = clean_video_title_from_filename(filename)
    return {
        "order": 999,
        "filename": filename,
        "title": f"{clean_title} | Görsel Matematik İspatı",
        "topic": "Matematik ve Geometri",
        "summary": (
            f"{clean_title} konusunun formüllerini ezberlemek yerine, "
            f"arkasındaki geometrik ve matematiksel mantığı adım adım görsel animasyonla keşfediyoruz."
        ),
        "question": f"{clean_title} konusunda sizin en çok dikkat ettiğiniz püf noktası nedir? Yorumlarda buluşalım! 👇",
        "hashtags": (
            "#matematik #geometri #tytmatematik #aytmatematik #yksmatematik "
            "#lgsmatematik #görselmatematik #ispat #mufithocailematematik #antalya"
        ),
    }


def format_caption(video_meta: dict, location_name: str = "Antalya") -> str:
    """Instagram Reels açıklama (caption) metnini oluşturur."""
    title = video_meta.get("title", "")
    summary = video_meta.get("summary", "")
    question = video_meta.get("question", "")
    hashtags = video_meta.get("hashtags", "")

    caption = (
        f"📐 {title}\n\n"
        f"✨ {summary}\n\n"
        f"🤔 {question}\n\n"
        f"📍 {location_name}\n"
        f"👨‍🏫 @mufithocailematematik\n\n"
        f"{hashtags}"
    )
    return caption.strip()


def is_already_uploaded_today(tracker_path: str):
    """Bugün (Türkiye saatiyle) zaten otomatik bir Reels paylaşılıp paylaşılmadığını kontrol eder."""
    if not os.path.exists(tracker_path):
        return False, None
    try:
        with open(tracker_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        today_str = now_trt().strftime("%Y-%m-%d")
        for item in reversed(data.get("history", [])):
            up_at = item.get("uploaded_at", "")
            if up_at.startswith(today_str) and item.get("status") != "manual":
                try:
                    up_hour = int(up_at[11:13])
                except Exception:
                    up_hour = 18
                if up_hour >= 6:
                    return True, item.get("filename")
    except Exception as e:
        print("Uyarı: Takip geçmişi kontrol edilirken hata:", e)
    return False, None


def find_next_video_in_queue(catalog_path: str, videos_dir: str, tracker_path: str):
    """
    Sıradaki paylaşılacak videoyu bulur:
    1. Önce reels_katalogu.json içindeki sırayı (1..38) takip eder.
    2. Katalogdaki videolar bittiğinde REELS_VIDEOLARI klasörüne sonradan eklenmiş yeni .mp4 dosyalarını sırayla alır.
    """
    uploaded_files = set()
    if os.path.exists(tracker_path):
        try:
            with open(tracker_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                uploaded_files = set(data.get("uploaded_files", []))
        except Exception:
            pass

    catalog_videos = []
    default_location = "Antalya"
    default_location_id = DEFAULT_ANTALYA_LOCATION_ID

    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as f:
            cat_data = json.load(f)
            catalog_videos = cat_data.get("videos", [])
            default_location = cat_data.get("default_location", "Antalya")
            default_location_id = cat_data.get("default_location_id", DEFAULT_ANTALYA_LOCATION_ID)

    # 1. Katalog sırasına göre kontrol et
    catalog_filenames = set()
    for item in sorted(catalog_videos, key=lambda x: x.get("order", 999)):
        fname = item.get("filename")
        if not fname:
            continue
        catalog_filenames.add(fname)
        full_path = os.path.join(videos_dir, fname)
        if os.path.exists(full_path) and fname not in uploaded_files:
            return item, full_path, default_location, default_location_id, len(uploaded_files)

    # 2. Klasöre yeni eklenmiş (katalog dışı) videoları kontrol et
    if os.path.isdir(videos_dir):
        extra_files = sorted([
            f for f in os.listdir(videos_dir)
            if f.lower().endswith(".mp4") and f not in catalog_filenames
        ])
        for fname in extra_files:
            if fname not in uploaded_files:
                meta = build_fallback_metadata(fname)
                full_path = os.path.join(videos_dir, fname)
                return meta, full_path, default_location, default_location_id, len(uploaded_files)

    return None, None, default_location, default_location_id, len(uploaded_files)


def load_ig_credentials() -> dict:
    """
    GitHub Secrets (IG_TOKEN_JSON) veya yerel ig_token.json dosyasından
    Instagram Graph API kimlik bilgilerini yükler.
    """
    creds = None
    env_json = os.getenv("IG_TOKEN_JSON")
    if env_json:
        try:
            creds = json.loads(env_json)
        except Exception as e:
            print("Uyarı: IG_TOKEN_JSON ortam değişkeni JSON olarak okunamadı:", e)

    if not creds and os.path.exists(TOKEN_FILE_DEFAULT):
        with open(TOKEN_FILE_DEFAULT, "r", encoding="utf-8") as f:
            creds = json.load(f)

    if not creds:
        # Tekil ortam değişkenlerini de destekle
        token = os.getenv("IG_ACCESS_TOKEN") or os.getenv("META_ACCESS_TOKEN")
        ig_user_id = os.getenv("IG_USER_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID")
        if token and ig_user_id:
            creds = {
                "access_token": token,
                "ig_user_id": ig_user_id,
                "location_id": os.getenv("IG_LOCATION_ID", DEFAULT_ANTALYA_LOCATION_ID),
                "github_repo": os.getenv("GITHUB_REPOSITORY", "hizarci84-dot/instagram-reels-otomasyon")
            }

    if not creds or not creds.get("access_token") or not creds.get("ig_user_id"):
        raise RuntimeError(
            "Instagram API kimlik bilgileri bulunamadı!\n"
            "Lütfen önce 'giris_yap.bat' (python auth_instagram.py) çalıştırarak ig_token.json oluşturun "
            "ve GitHub deponuzun Secrets bölümüne IG_TOKEN_JSON olarak ekleyin."
        )

    # Eğer app_id ve app_secret mevcutsa token süresini otomatik tazele
    app_id = creds.get("app_id")
    app_secret = creds.get("app_secret")
    if app_id and app_secret:
        try:
            ex_res = graph_api_request(
                f"{GRAPH_BASE_URL}/oauth/access_token",
                method="GET",
                data={
                    "grant_type": "fb_exchange_token",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "fb_exchange_token": creds["access_token"],
                },
                timeout=15,
            )
            if ex_res.get("access_token"):
                creds["access_token"] = ex_res["access_token"]
        except Exception:
            pass

    return creds


def graph_api_request(url: str, method: str = "GET", data: dict = None, headers: dict = None, raw_body: bytes = None, timeout: int = 120) -> dict:
    """Meta Graph API'ye HTTP isteği gönderir ve JSON yanıtını döndürür."""
    req_headers = headers.copy() if headers else {}
    body_bytes = raw_body

    if data is not None and raw_body is None:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        if method.upper() == "GET":
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{encoded.decode('utf-8')}"
        else:
            body_bytes = encoded
            req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_text = resp.read().decode("utf-8")
            return json.loads(raw_text) if raw_text else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Graph API Hatası (HTTP {e.code}): {err_body}") from e


def resolve_antalya_location_id(access_token: str, fallback_id: str) -> str:
    """
    Antalya konum ID'sini döndürür. Eğer token üzerinden dinamik arama yapılabiliyorsa doğrular,
    yapılamıyorsa varsayılan Antalya Facebook/Instagram Place ID'sini kullanır.
    """
    try:
        res = graph_api_request(
            f"{GRAPH_BASE_URL}/pages/search",
            method="GET",
            data={
                "q": "Antalya",
                "fields": "id,name,location",
                "access_token": access_token
            },
            timeout=15
        )
        items = res.get("data", [])
        for item in items:
            if "antalya" in item.get("name", "").lower():
                return str(item["id"])
    except Exception:
        pass
    return fallback_id or DEFAULT_ANTALYA_LOCATION_ID


def create_resumable_reels_container(ig_user_id: str, access_token: str, caption: str, location_id: str) -> tuple:
    """
    Instagram Graph API üzerinde Resumable (Doğrudan Dosya Yüklemeli) Reels konteyneri oluşturur.
    Eğer location_id yetki/bölge nedeniyle reddedilirse otomatik olarak location_id olmadan tekrar dener.
    """
    params = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "share_to_feed": "true",
        "access_token": access_token,
    }
    if location_id:
        params["location_id"] = location_id

    try:
        res = graph_api_request(f"{GRAPH_BASE_URL}/{ig_user_id}/media", method="POST", data=params)
        return res.get("id"), res.get("uri")
    except Exception as e:
        if location_id:
            print(f"  [Bilgi] Konum ID ({location_id}) ile konteyner oluşturulamadı ({e}).")
            print("  [Bilgi] Konum bilgisi açıklamada ('📍 Antalya') korunarak devam ediliyor...")
            params.pop("location_id", None)
            res = graph_api_request(f"{GRAPH_BASE_URL}/{ig_user_id}/media", method="POST", data=params)
            return res.get("id"), res.get("uri")
        raise


def upload_binary_to_rupload(container_id: str, upload_uri: str, access_token: str, file_path: str):
    """Yerel .mp4 dosyasını doğrudan Meta rupload sunucusuna yükler."""
    target_url = upload_uri or f"{RUPLOAD_BASE_URL}/{container_id}"
    file_size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        video_bytes = f.read()

    headers = {
        "Authorization": f"OAuth {access_token}",
        "offset": "0",
        "file_size": str(file_size),
        "Content-Type": "application/octet-stream",
    }

    print(f"  Video dosyası Meta sunucularına yükleniyor ({file_size / (1024 * 1024):.2f} MB)...")
    res = graph_api_request(target_url, method="POST", headers=headers, raw_body=video_bytes, timeout=300)
    return res


def create_url_reels_container(ig_user_id: str, access_token: str, video_url: str, caption: str, location_id: str) -> str:
    """Alternatif olarak GitHub Raw URL üzerinden Reels konteyneri oluşturur."""
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": access_token,
    }
    if location_id:
        params["location_id"] = location_id

    try:
        res = graph_api_request(f"{GRAPH_BASE_URL}/{ig_user_id}/media", method="POST", data=params)
        return res.get("id")
    except Exception:
        if location_id:
            params.pop("location_id", None)
            res = graph_api_request(f"{GRAPH_BASE_URL}/{ig_user_id}/media", method="POST", data=params)
            return res.get("id")
        raise


def wait_until_container_ready(container_id: str, access_token: str, max_polls: int = 35, poll_interval: int = 10):
    """Meta sunucularının videoyu işleyip 'FINISHED' durumuna getirmesini bekler."""
    print(f"  Instagram video işleme durumu kontrol ediliyor (Container ID: {container_id})...")
    for attempt in range(1, max_polls + 1):
        res = graph_api_request(
            f"{GRAPH_BASE_URL}/{container_id}",
            method="GET",
            data={"fields": "status_code,status", "access_token": access_token},
            timeout=30,
        )
        status_code = res.get("status_code", "UNKNOWN")
        status_detail = res.get("status", "")
        print(f"    [{attempt}/{max_polls}] Durum: {status_code} {f'({status_detail})' if status_detail else ''}")

        if status_code == "FINISHED":
            return True
        if status_code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram video işleme hatası: {res}")

        time.sleep(poll_interval)

    raise TimeoutError("Instagram video işleme süresi zaman aşımına uğradı.")


def publish_reels_container(ig_user_id: str, container_id: str, access_token: str) -> tuple:
    """İşlenmesi tamamlanan Reels konteynerini yayına alır ve kalıcı bağlantısını (permalink) döndürür."""
    print("  Reels videosu yayına alınıyor (media_publish)...")
    res = graph_api_request(
        f"{GRAPH_BASE_URL}/{ig_user_id}/media_publish",
        method="POST",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=60,
    )
    media_id = res.get("id")
    permalink = f"https://www.instagram.com/mufithocailematematik/"

    if media_id:
        try:
            info = graph_api_request(
                f"{GRAPH_BASE_URL}/{media_id}",
                method="GET",
                data={"fields": "permalink,shortcode", "access_token": access_token},
                timeout=20,
            )
            if info.get("permalink"):
                permalink = info["permalink"]
        except Exception:
            pass

    return media_id, permalink


def send_ntfy_notification(title: str, message: str, topic: str = "mufithoca_matematik_bildirim"):
    """Paylaşım tamamlandığında ntfy.sh üzerinden telefona bildirim gönderir (opsiyonel)."""
    if not topic:
        return
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title.encode("utf-8"), "Tags": "clapper,math,white_check_mark"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Instagram Reels Günlük Otomatik Paylaşım Sistemi")
    parser.add_argument("--dry-run", action="store_true", help="Paylaşım yapmadan sıradaki videoyu ve açıklamasını test eder")
    parser.add_argument("--force", action="store_true", help="Bugün zaten paylaşım yapılmış olsa bile zorla paylaşır")
    parser.add_argument("--tracker", default=TRACKER_FILE_DEFAULT, help="Yüklenen videolar takip dosyası")
    args = parser.parse_args()

    print("\n" + "=" * 68)
    print(" INSTAGRAM REELS OTOMATİK PAYLAŞIM SİSTEMİ (@mufithocailematematik)")
    print(f" Tarih / Saat (TSİ): {now_trt().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 68)

    if not args.force and not args.dry_run:
        already_done, uploaded_name = is_already_uploaded_today(args.tracker)
        if already_done:
            print(f"\n[BİLGİ] Bugün zaten bir Reels videosu paylaşıldı: '{uploaded_name}'")
            print("Günde 1 Reels kuralına uygun olarak bu çalışma tamamlandı sayılıyor.")
            print("(Ek paylaşım yapmak isterseniz --force parametresini kullanabilirsiniz).\n")
            return

    video_meta, full_path, location_name, default_loc_id, done_count = find_next_video_in_queue(
        CATALOG_FILE, VIDEOS_DIR, args.tracker
    )

    if not video_meta or not full_path:
        print("\n🎉 Tebrikler! Katalogdaki ve klasördeki tüm Reels videoları paylaşıldı!")
        return

    filename = video_meta["filename"]
    caption = format_caption(video_meta, location_name=location_name)
    file_size_mb = os.path.getsize(full_path) / (1024 * 1024)

    print(f"\n▶ Sıradaki Video (#{done_count + 1}) : {filename} ({file_size_mb:.2f} MB)")
    print(f"▶ Konu Başlığı          : {video_meta.get('title')}")
    print(f"▶ Konum                 : {location_name} (ID: {default_loc_id})")
    print("-" * 68)
    print("OTOMATİK OLUŞTURULAN AÇIKLAMA (CAPTION):")
    print("-" * 68)
    print(caption)
    print("-" * 68)

    if args.dry_run:
        print("\n[TEST MODU / DRY-RUN] Gerçek paylaşım yapılmadı. Kurulum ve içerik hazır!")
        return

    creds = load_ig_credentials()
    access_token = creds["access_token"]
    ig_user_id = str(creds["ig_user_id"])
    location_id = str(creds.get("location_id") or resolve_antalya_location_id(access_token, default_loc_id))
    github_repo = creds.get("github_repo") or os.getenv("GITHUB_REPOSITORY", "hizarci84-dot/instagram-reels-otomasyon")

    # 1. GitHub Raw URL üzerinden Reels medya konteyneri oluştur (En hızlı ve kararlı yöntem)
    container_id = None
    raw_url = f"https://raw.githubusercontent.com/{github_repo}/main/{VIDEOS_DIR}/{urllib.parse.quote(filename)}"
    try:
        print(f"\n[1/3] Instagram Reels medya konteyneri oluşturuluyor (GitHub Bulut URL)...")
        print(f"  Video Kaynağı: {raw_url}")
        container_id = create_url_reels_container(
            ig_user_id=ig_user_id,
            access_token=access_token,
            video_url=raw_url,
            caption=caption,
            location_id=location_id,
        )
    except Exception as url_err:
        print(f"  ! URL üzerinden yükleme uyarısı: {url_err}")
        print("  --> Yedek yöntem (Doğrudan Dosya Yükleme) devreye alınıyor...")
        container_id, upload_uri = create_resumable_reels_container(
            ig_user_id=ig_user_id,
            access_token=access_token,
            caption=caption,
            location_id=location_id,
        )
        upload_binary_to_rupload(container_id, upload_uri, access_token, full_path)

    # 2. Konteyner işlenene kadar bekle
    print("\n[2/3] Video işleme durumu bekleniyor...")
    wait_until_container_ready(container_id, access_token)

    # 3. Yayına al
    print("\n[3/3] Reels videosu yayınlanıyor...")
    media_id, permalink = publish_reels_container(ig_user_id, container_id, access_token)

    # 4. Takip dosyasını güncelle
    if os.path.exists(args.tracker):
        with open(args.tracker, "r", encoding="utf-8") as f:
            tracker_data = json.load(f)
    else:
        tracker_data = {"uploaded_files": [], "history": []}

    if filename not in tracker_data.setdefault("uploaded_files", []):
        tracker_data["uploaded_files"].append(filename)

    tracker_data.setdefault("history", []).append({
        "filename": filename,
        "title": video_meta.get("title"),
        "media_id": media_id,
        "permalink": permalink,
        "location": location_name,
        "location_id": location_id,
        "uploaded_at": now_trt().isoformat(),
    })

    with open(args.tracker, "w", encoding="utf-8") as f:
        json.dump(tracker_data, f, indent=2, ensure_ascii=False)

    with open("last_uploaded.txt", "w", encoding="utf-8") as f:
        f.write(f"{filename} -> {permalink}\n")

    send_ntfy_notification(
        title="Yeni Reels Paylaşıldı! (@mufithocailematematik)",
        message=f"{video_meta.get('title')}\nKonum: {location_name}\nLink: {permalink}",
    )

    print("\n" + "=" * 68)
    print(" ✅ REELS BAŞARIYLA PAYLAŞILDI!")
    print(f" Video     : {filename}")
    print(f" Başlık    : {video_meta.get('title')}")
    print(f" Konum     : {location_name}")
    print(f" Instagram : {permalink}")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()
