# 📐 Instagram Reels Günlük Otomatik Paylaşım Sistemi (`@mufithocailematematik`)

Bu proje, Masaüstündeki **Wox Tarzı Reels (9x16)** klasöründe yer alan **38 benzersiz matematik ve geometri animasyonunu** her gün Türkiye saatiyle **18:00'de** otomatik olarak **Instagram Reels** formatında paylaşan bir **GitHub Actions + Resmi Instagram Graph API** bulut otomasyonudur.

## ✨ Temel Özellikler
- **30 Gün Sınırı Yoktur:** Instagram mobil uygulamasındaki 29–30 günlük planlama sınırına takılmaz; 38 videonun tamamını (ve sonradan ekleyeceğiniz yeni videoları) her gün saat **18:00'de** sırayla yayınlar.
- **Bilgisayar & Telefon Kapalıyken Çalışır:** GitHub sunucuları üzerinde her gün otomatik tetiklenir (`18:00 TSİ` ana çalışma + `19:00`, `20:00`, `21:00` yedek güvenlik ağları).
- **Otomatik Konu Özeti + Etkileşim Sorusu:** Her videonun konusuna özel hazırlanmış merak uyandırıcı matematiksel özet, yorumlarda etkileşim başlatan soru ve konu etiketleri (`reels_katalogu.json`) otomatik eklenir.
- **Otomatik Konum (Antalya):** Tüm paylaşımlarda konum olarak **Antalya** (`location_id` + `📍 Antalya`) otomatik tanımlanır.
- **Çift Videolar Temizlendi:** Klasördeki 43 videodan eski/tekrar olan 5 versiyon (`bolunebilme_3_9_neural`, `dogum_gunu_paradoksu_final`, `thales_teoremi_final`, `pascal_fraktal_final`, `final_ders_videosu`) ayıklanarak **38 tekil ve en güncel video** sıraya dizilmiştir.

---

## 🚀 Kurulum (Sadece 1 Kez Yapılır - 2 Dakika)

### 1. Meta Graph API Token Alma
1. Tarayıcınızdan [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) sayfasını açın.
2. Sağ taraftaki **Permissions (İzinler)** kısmından şu 4 izni seçin:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
3. **Generate Access Token** butonuna tıklayıp `@mufithocailematematik` hesabınızın bağlı olduğu sayfayı onaylayın.

### 2. `giris_yap.bat` ile Token'ı Kaydetme
1. Proje klasöründeki **`giris_yap.bat`** dosyasına çift tıklayın.
2. Kopyaladığınız Token'ı yapıştırıp Enter'a basın.
3. Sihirbaz otomatik olarak `@mufithocailematematik` hesap ID'nizi ve **Antalya** konum ID'sini bulup `ig_token.json` dosyasını oluşturacak ve içeriğini **panoya kopyalayacaktır**.

### 3. GitHub Secrets'a Yapıştırma
1. GitHub deponuzda **Settings** -> **Secrets and variables** -> **Actions** bölümüne girin.
2. **New repository secret** butonuna tıklayın:
   - **Name:** `IG_TOKEN_JSON`
   - **Secret:** `Ctrl + V` (Panodaki veriyi yapıştırın)
3. **Add secret** butonuna tıklayın. Artık sistem her gün saat **18:00'de** tamamen otomatik çalışacaktır!

---

## 🛠️ Kısayol Dosyaları
- **`test_onizleme.bat`**: Paylaşım yapmadan sıradaki videoyu, otomatik oluşturulan açıklamayı ve Antalya konum bilgisini ekranda gösterir.
- **`giris_yap.bat`**: Instagram Graph API Token kurulum sihirbazını başlatır.
- **`token_kopyala.bat`**: `ig_token.json` içeriğini GitHub Secrets'a yapıştırmak için panoya kopyalar.
- **`hemen_siradakini_yukle.bat`**: Saat 18:00'i beklemeden sıradaki videoyu anında Instagram'da paylaşır.
- **`yeni_videolari_gonder.bat`**: Masaüstündeki `Wox Tarzı Reels (9x16)` klasörüne yeni videolar eklediğinizde tek tıkla GitHub'a gönderir.
