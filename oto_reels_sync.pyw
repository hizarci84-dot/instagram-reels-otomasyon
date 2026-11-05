# -*- coding: utf-8 -*-
"""
Instagram Reels Otomatik Arka Plan Klasör İzleyici ve GitHub Senkronizasyon Servisi
Masaüstündeki 'Wox Tarzı Reels (9x16)' klasörüne yeni bir video düştüğünde:
1. Dosya yazımının tamamlanmasını bekler ve REELS_VIDEOLARI klasörüne kopyalar.
2. Varsa altyazı (.ass / .srt) dosyasından konunun özetini çıkarıp reels_katalogu.json'a ekler.
3. Otomatik olarak GitHub'a (hizarci84-dot/instagram-reels-otomasyon) commit ve push yapar.
"""

import os
import sys
import re
import time
import json
import shutil
import subprocess

PROJECT_DIR = r"C:\Users\hizar\OneDrive\Desktop\projeler\INSTAGRAM REELS OTOMASYON"
SOURCE_REELS_DIR = r"C:\Users\hizar\OneDrive\Desktop\Wox Tarzı Reels (9x16)"
WOX_SUBS_DIR = r"C:\Users\hizar\OneDrive\Desktop\projeler\wox tarzı animasyon\videolar"
DEST_VIDEOS_DIR = os.path.join(PROJECT_DIR, "REELS_VIDEOLARI")
CATALOG_FILE = os.path.join(PROJECT_DIR, "reels_katalogu.json")

SKIP_FILES = {
    "bolunebilme_3_9_neural.mp4",
    "dogum_gunu_paradoksu_final.mp4",
    "thales_teoremi_final.mp4",
    "pascal_fraktal_final.mp4",
    "final_ders_videosu.mp4",
}

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def wait_for_file_ready(filepath: str, timeout: int = 60) -> bool:
    """Dosyanın yazılmasının/kopyalanmasının tamamlanmasını bekler."""
    start = time.time()
    last_size = -1
    stable = 0
    while time.time() - start < timeout:
        if not os.path.exists(filepath):
            time.sleep(1)
            continue
        try:
            sz = os.path.getsize(filepath)
            if sz > 100 * 1024 and sz == last_size:
                stable += 1
                if stable >= 2:
                    return True
            else:
                stable = 0
            last_size = sz
        except Exception:
            stable = 0
        time.sleep(1.5)
    return False


def clean_title_from_filename(filename: str) -> str:
    name, _ = os.path.splitext(filename)
    clean = re.sub(r"^\d+[\s\-_.]*", "", name)
    clean = re.sub(r"_final(_raw)?$", "", clean, flags=re.IGNORECASE)
    clean = clean.replace("_", " ").strip()
    return re.sub(r"\s+", " ", clean).title()


def extract_summary_from_subtitles(filename: str) -> str:
    """Eğer wox tarzı animasyon klasöründe .ass veya .srt altyazısı varsa ilk cümlelerinden özet çıkarır."""
    base, _ = os.path.splitext(filename)
    ass_path = os.path.join(WOX_SUBS_DIR, f"{base}.ass")
    if os.path.exists(ass_path):
        try:
            lines = []
            with open(ass_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("Dialogue:"):
                        parts = line.split(",", 9)
                        if len(parts) == 10:
                            txt = parts[9].replace("\\N", " ").replace("\\n", " ").strip()
                            txt = re.sub(r"\{[^}]*\}", "", txt).strip()
                            if txt:
                                lines.append(txt)
            if lines:
                summary = " ".join(lines[:3])
                if len(summary) > 240:
                    summary = summary[:237].rsplit(" ", 1)[0] + "..."
                return summary
        except Exception:
            pass
    return ""


def add_to_catalog_if_missing(filename: str):
    """Yeni videoyu otomatik açıklama, etkileşim sorusu ve Antalya konumuyla reels_katalogu.json'a ekler."""
    if not os.path.exists(CATALOG_FILE):
        return
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            cat_data = json.load(f)
    except Exception:
        return

    videos = cat_data.setdefault("videos", [])
    for v in videos:
        if v.get("filename") == filename:
            return

    max_order = max((v.get("order", 0) for v in videos), default=0)
    clean_title = clean_title_from_filename(filename)
    sub_summary = extract_summary_from_subtitles(filename)
    if not sub_summary:
        sub_summary = (
            f"{clean_title} konusunun formüllerini ezberlemek yerine, "
            f"arkasındaki geometrik ve matematiksel mantığı görsel animasyonla adım adım keşfediyoruz."
        )

    new_entry = {
        "order": max_order + 1,
        "filename": filename,
        "title": f"{clean_title} | Görsel Matematik İspatı",
        "topic": "Matematik ve Geometri",
        "summary": sub_summary,
        "question": f"{clean_title} konusunda sizin aklınıza ilk hangi kural veya yöntem geliyor? Yorumlarda buluşalım! 👇",
        "hashtags": "#matematik #geometri #tytmatematik #aytmatematik #yksmatematik #lgsmatematik #görselispat #mufithocailematematik #antalya",
    }
    videos.append(new_entry)

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(cat_data, f, indent=2, ensure_ascii=False)


def sync_once() -> bool:
    """Masaüstündeki Wox Tarzı Reels (9x16) klasörünü tarar, yeni videoları kopyalayıp GitHub'a gönderir."""
    if not os.path.exists(SOURCE_REELS_DIR):
        return False

    os.makedirs(DEST_VIDEOS_DIR, exist_ok=True)
    os.chdir(PROJECT_DIR)

    # 1. Önce GitHub'daki son durumu (yuklenenler.json vb.) çek
    subprocess.run(
        ["git", "pull", "--rebase", "origin", "main"],
        capture_output=True,
        creationflags=CREATE_NO_WINDOW,
    )

    added_any = False
    for fname in sorted(os.listdir(SOURCE_REELS_DIR)):
        if not fname.lower().endswith(".mp4"):
            continue
        if fname in SKIP_FILES or fname.endswith(".tmp.mp4") or fname.endswith("_raw.mp4"):
            continue

        src_path = os.path.join(SOURCE_REELS_DIR, fname)
        dst_path = os.path.join(DEST_VIDEOS_DIR, fname)

        need_copy = False
        if not os.path.exists(dst_path):
            need_copy = True
        else:
            # Eğer kaynak dosya güncellenmişse ve boyutu farklıysa
            try:
                if abs(os.path.getsize(src_path) - os.path.getsize(dst_path)) > 1024 and os.path.getmtime(src_path) > os.path.getmtime(dst_path):
                    need_copy = True
            except Exception:
                pass

        if need_copy and wait_for_file_ready(src_path):
            shutil.copy2(src_path, dst_path)
            add_to_catalog_if_missing(fname)
            added_any = True

    # 2. Git'te değişiklik varsa otomatik commit ve push yap
    status_res = subprocess.run(
        ["git", "status", "--porcelain", "REELS_VIDEOLARI", "reels_katalogu.json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        creationflags=CREATE_NO_WINDOW,
    )
    if status_res.stdout.strip():
        subprocess.run(["git", "add", "REELS_VIDEOLARI", "reels_katalogu.json"], capture_output=True, creationflags=CREATE_NO_WINDOW)
        subprocess.run(
            ["git", "commit", "-m", "Otomatik: Yeni uretilen Wox 9x16 Reels videosu eklendi"],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
        )
        subprocess.run(["git", "push", "origin", "main"], capture_output=True, creationflags=CREATE_NO_WINDOW)
        return True

    return added_any


if __name__ == "__main__":
    if "--once" in sys.argv:
        sync_once()
        sys.exit(0)

    # İlk açılışta hemen kontrol et
    try:
        sync_once()
    except Exception:
        pass

    # Bilgisayar açık olduğu sürece her 10 dakikada bir yeni video var mı kontrol et
    while True:
        time.sleep(600)
        try:
            sync_once()
        except Exception:
            pass
