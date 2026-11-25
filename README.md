# Global Trend Radar AI — v0.1 pilot

**Durum: geliştirme paketi; üretim otomasyonu henüz doğrulanmadı.** 26 Kasım 2026 (TR).

Global haber/trend sinyallerinin merkezi, özel amaçlı ve metaveriyle sınırlı toplayıcısı. Tam haber veya ücretli makale gövdesi çekmez; veri tabanına kaynak kimliği, başlık, URL, varsa yayın tarihi ve kaynak tarafından bildirilen ham sinyal yazılır. Ücretli LLM gerekmez. GitHub araması Trending listesi değildir.

## Başlangıç

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate; Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pytest
python -m pytest -q
python radar.py collect
python radar.py health
python radar.py report --days 1
python radar.py export --days 7 > private-export.json
```

Varsayılan yerel SQLite test içindir. Gerçek üretimde `--require-db` eksik bağlantıyı hata sayar. `schema.sql` yalnızca proje sahibi tarafından bir kez uygulanır; Neon pilotunda uygulanmıştır. PostgreSQL uygulama rolü DDL yapmaz. Veri tabanı dışında başka sistemlere yazılmaz.

## Gerçek Neon altyapısı

- Free organizasyon: `org-icy-cake-74628211`.
- Proje: `global-trend-radar-ai-free`, `[private project ID]`; bölge `aws-us-east-1`; compute 0.25 CU sabit.
- Branch `main`, veritabanı `trend_radar`, rol `radar_app` (read_write, DDL yok).
- SQL ile doğrulanan başlangıç: 20 kamuya açık GitHub arama kaydı, 1 `manual_verified` kaynak kaydı, 0 teslimat. Uygulama cron çalıştırması değildir.
- Bağlantı: Neon Console > Connect > `trend_radar` > `radar_app` > pooled connection string. URL'yi yalnızca GitHub Actions secret `DATABASE_URL` olarak ekle, mesajlara veya dosyaya yapıştırma. `sslmode=require` kullanılır.

## GitHub ve otomasyon

1. `https://github.com/new` üzerinden `global-trend-radar-ai` adlı boş depo oluştur. Kullanıcı hesabı `emirhankaya985-cloud`. Public standart runner ücretsizdir; yalnızca kod ve genel yapılandırma yayımlanabilir. Özel veriler asla repoya veya artifact'a gönderilmez. Private tercihinde hesaptaki ortak Actions bütçesini doğrula; ücretli aşım bütçesi sıfır olmalıdır.
2. Paketi aç ve repoya yükle (gizli `.github` klasörü dahil). Örnek:
   `git init -b main`, `git add .`, `git commit -m "Initial radar pilot"`, `git remote add origin https://github.com/emirhankaya985-cloud/global-trend-radar-ai.git`, `git push -u origin main`.
3. Settings > Secrets and variables > Actions > New repository secret: `DATABASE_URL`, bildirim için `NTFY_TOPIC` (rastgele en az 16 karakter; mümkünse erişim kontrollü konu ve `NTFY_TOKEN`). Telegram alternatifinde `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Kimlik bilgilerini saklı tut. Ücretsiz ntfy.sh konularının varsayılan olarak gizlilik garantisi yoktur; özel bülten içeriğini göndermeyin.
4. Actions > Global Trend Radar > Run workflow. `health` çıktısı ile gerçek başarılı fetch, yeni kayıt, hata ve teslimat sayısını kontrol et. Birden çok kaynaktan gerçek veri gelmeden üretim onayı verme.
5. Settings > Secrets and variables > Actions > Variables: `RADAR_SCHEDULE_ENABLED=true` yalnızca ilk başarılı manuel çalıştırma ve bütçe kontrolünden sonra. Varsayılan kapalı. GitHub gecikmesi nedeniyle saat kesinliği yoktur.

Saatlik tarama UTC :17. Günlük rapor 05 UTC (08 TR), pazartesi haftalık, ayın 1'inde 30 günlük rapor. Bu ilk sürümde geciken cron rapor atlayabilir; raporlar UTC çalıştırma saatine bağlıdır. Çok kaynaklı aday sinyaller saatlik en çok üç yeni teslimat grubuna ayrılır; gerçek zamanlı haber teyidi değildir. Kanal makbuzu yoksa `sent` sayılmaz. Belirsiz gönderim yeniden denenmez; manuel inceleme gerektirir.

## Analiz

- URL izleme parametreleri temizlenir; kaynak/URL benzersizdir. Benzer başlıklar Jaccard ile yaklaşık gruplandırılır; aynı olayın farklı ifadeleri kaçabilir. 30 günlük rapor en yeni 5000 kaydı gruplar; ham toplam tam sayılır.
- Kategoriler anahtar kelime ve kaynak varsayılanına göre. Güven etiketleri kaynak türüdür, haber doğruluk puanı değildir. Önceki gözlem dönemi mevcut değilse eğilim bilinmiyor. Ham kayıt farkı arama hacmi veya satış değildir; kesintiler karşılaştırmayı bozabilir.
- Fırsat hipotezleri iki ayrı kaynak sinyali gerektirir; marka/telif, talep ve kârlılık ayrıca doğrulanmalıdır.
- Türkçe rapor şablonu otomatik; özgün haber başlığı İngilizce kalabilir. Yerel Argos Translate ve lisansı doğrulanmış EN→TR modelini kurarsanız `python radar.py report --days 1 --translate` seçeneği başlık çevirisini dener. Model kurulmadı/test edilmedi; tam makale Türkçe özeti bu sürümde yoktur. Paid AI API zorunluluğu yoktur.

## Sınırlar / güvenlik

7 kaynak yapılandırılmış etkin aday, 6 pasif aday. RSS canlı testi yerel DNS engeline takıldı; her biri ilk CI koşusunda test edilmelidir. Kaynak kullanımı kişisel araştırmayla sınırlıdır; kamusal dağıtım/ticari kullanım izni varsayılmaz. HTTP yönlendirmesi takip edilmez, 12 saniye timeout, 2 MB yanıt, 50 feed öğesi, 20 GitHub öğesi, ETag/Last-Modified, hata dahil kaynak aralığı, XML entity engeli, bütçe koruması (700 MiB/150k öğe/100k fetch, silme yok). Kurulumda GitHub token isteğe bağlı olarak yalnızca GitHub API adresine gönderilir. GitHub Actions maksimum 4 dakika, 31 günde 744 saatlik çalıştırma; private hesap için üst sınır 2976 dakika (CI hariç), bu nedenle public kod deposu veya kontrollü daha seyrek cron gerekir. Neon 100 CU-hour/ay, 1 GB/proje sınırına göre kullanım izlenmeli; otomatik maliyet/fatura doğrulaması henüz yoktur. Gmail erişimi ve Etsy/Reddit/YouTube API'leri etkin değil.

Diğer projeler için `export` komutu sürümlü JSON, `health` komutu metaveri üretir; gelecekte salt okunur rol veya servis aracılığıyla erişim. Şimdilik başka hiçbir depo veya DB değiştirilmedi. Çıktılar özel tutulmalı; ham bülten içeriği asla ortak depoya taşınmamalıdır.

Ayrıntılar: [Kaynak araştırması](docs/SOURCES.md), [Checkpoint](CHECKPOINT.md).
