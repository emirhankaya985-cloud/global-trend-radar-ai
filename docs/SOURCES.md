# Kaynak ve açık kaynak bileşen araştırması — 26.11.2026

Bu dokümanda erişim yöntemi adaylarının varlığı, veri çekme başarısı ve kullanım izni farklı şeylerdir. Kaynakların tümünü üretimde açmadan önce kullanım koşulları ve canlı yanıtlar kontrol edilmelidir. Full-text arşivleme yoktur.

| Kaynak | Önerilen yöntem | Pilot durumu |
|---|---|---|
| Bloomberg | [Bültenler](https://bloomberg.com/newsletters), `https://www.bloomberg.com/feeds/markets/news.rss` aday RSS | Pasif: koşul/yanıt incelemesi; paywall yok |
| Financial Times | `https://www.ft.com/rss/home/international` aday RSS | Pasif: kişisel kullanım sınırları ve yanıt doğrulanacak |
| Goldman Sachs | [Briefings](https://www.goldmansachs.com/briefings) e-posta | Abonelik ve gönderen onayı gerekli |
| Morgan Stanley | [Five Ideas](https://www.morganstanley.com/insights/our-series) e-posta | Abonelik ve gönderen onayı gerekli |
| Reuters | Lisanslı açık erişim veya izinli bülten; eski genel RSS 2020'de kapanmış (https://feeder.co/knowledge-base/rss-content/reuters-rss-feeds/) | Pasif; Reuters yatırımcı RSS kurumsal haber, genel ajans haberi değil |
| NYT | `https://rss.nytimes.com/services/xml/rss/nyt/World.xml` aday RSS | Pasif: lisans ve kişisel kullanım incelemesi |
| Foreign Affairs | https://www.foreignaffairs.com/ üzerinden bülten | Bülten erişimi ve izin incelemesi, aktif değil |
| Substack | Yazarın herkese açık yayınında `/feed` aday; abonelikte izinli e-posta | Tek tek yayın ve koşul doğrulaması |
| 1440 | [Daily Digest](https://join1440.com/) bülteni | Abonelik gerekli |
| Google Trends | `https://trends.google.com/trending/rss?geo=TR` ve US; [API alpha](https://developers.google.com/search/apis/trends) başvuru | 2 RSS aday etkin; web XML türü gördü, yerel DNS nedeniyle ayrıştırma yok; değerler yaklaşık hacim etiketi |
| Reddit | [Onaylı Data API](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) | Pasif; erişim izni ve ticari kullanım için ayrıca yazılı onay; silme politikası gerekli |
| Hacker News | [Resmi API](https://github.com/HackerNews/API) veya https://news.ycombinator.com/rss | RSS etkin aday; web RSS türü görüldü; uygulama canlı veri yok |
| GitHub | [Search REST API](https://docs.github.com/en/rest/search/search#search-repositories), GitHub Blog RSS | Search: 20 gerçek manuel kayıt; Blog: aday. Trending sıralaması değil. |
| YouTube | [videos.list](https://developers.google.com/youtube/data/reference/rest/v3/videos/list) `chart=mostPopular`, 1 kota birimi; bölge/kategori | API anahtarı gerekli, pasif; metadata saklama/güncelleme kuralları |
| OpenAI | https://openai.com/news/rss.xml | Etkin aday; web XML türü görüldü; uygulama canlı veri yok |
| Anthropic | [Newsroom](https://www.anthropic.com/news), resmî bülten/izinli duyuru | Pasif: RSS/API teyidi yok |
| Perplexity | [Blog](https://www.perplexity.ai/tr/hub/blog), izinli bülten | Pasif: RSS teyidi yok; ücretli API şart değil |
| Etsy | [Open API v3](https://developer.etsy.com/documentation/), onaylı uygulama; satıcı raporu veya kullanıcının sağladığı CSV | Pasif: API şartları ekran scraping'ini yasaklıyor; satış hacmi uydurulmaz |
| Shopify | [Atom blog](https://help.shopify.com/en/manual/online-store/blogs/publishing-blogs), kendi mağazasının izinli API'si | Blog aday pasif, rakip satış verisi değil |
| BBC | https://feeds.bbci.co.uk/news/world/rss.xml | Aday, pasif: koşul ve yanıt incelemesi |
| Federal Reserve | https://www.federalreserve.gov/feeds/press_all.xml | Etkin aday; web XML türü görüldü |
| SEC | https://www.sec.gov/news/pressreleases.rss | Aday, pasif: resmi erişim ve User-Agent koşulu |
| FRED | https://fred.stlouisfed.org/docs/api/fred/ | Ücretsiz anahtar, veri serisi lisansları kontrol edilmeli |
| World Bank | https://data.worldbank.org/ / https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information | Aday: makro veri, izinli seri lisansı, frekans ve API erişim kontrolü |
| Eurostat | https://ec.europa.eu/eurostat/web/main/data/web-services | Aday: resmi AB veri serileri, trend olayları ile karıştırma |
| OECD | https://data-explorer.oecd.org/ | Aday: SDMX, seri ve kullanım koşulları |
| Google Trends BigQuery açık veri | https://cloud.google.com/bigquery/public-data | Aday: kota ve sorgu maliyeti doğrulanmadan devreye alma |
| arXiv | https://info.arxiv.org/help/api/index.html | Aday: araştırma trendleri, oran/metadata şartları |
| GitHub Blog | https://github.blog/feed/ | Etkin aday; web RSS türü görüldü |
| Etsy Seller Handbook | https://www.etsy.com/seller-handbook | Aday: manuel editoryal araştırma, kazanç kanıtı değildir |

## Açık kaynak incelemesi ve tercih

| Depo | Lisans / erişim | Değerlendirme |
|---|---|---|
| https://github.com/sansan0/TrendRadar | GPL-3.0 | Çok kaynaklı trend/RSS/ntfy, zamanlama ve birleşik bildirim açısından en yakın örnek. Lisans yükümlülükleri ve kaynak erişimi gözden geçirilmeden kod kopyalanmadı. |
| https://github.com/miniflux/v2 | Apache-2.0 | RSS/Atom + PostgreSQL, filtre/entegrasyon mimarisi, aktif upstream. Sürekli Go sunucusu gerektirdiği için pilotta kurulmadı. |
| https://github.com/FreshRSS/FreshRSS | AGPL-3.0 | Olgun kendi sunucunda okuyucu. PHP servis maliyeti ve ağ üzerinden kaynak yükümlülüğü nedeniyle kullanılmadı. |
| https://github.com/DIYgod/RSSHub | AGPL-3.0 | RSS üretici, kaynak başına kullanım koşulu belirsizliği ve servis ihtiyacı; scraping rotaları kapalı tutulur. |
| https://github.com/kurtmckee/feedparser | BSD-2-Clause | Uygun ve olgun parser. Çevrimdışı ortamda kurulu olmadığından bu pilotta `defusedxml` kullanıldı; geniş RSS uyumu için sonraki adım. |
| https://github.com/argosopentech/argos-translate | MIT veya CC0 | Yerel çeviri, model lisansları ayrıca denetlenmeli. Model ve bağımlılık kurulumu üretimde doğrulanmadı. |
| https://github.com/miso-belica/sumy | Lisans dağıtımında ayrıca kontrol | Extractive summarization, yalnızca izinli tam metin için ileride değerlendir. Şu an başlık metaverisi var. |
| https://github.com/assafelovic/gpt-researcher | Apache-2.0 | Araştırma planlama/ajan yaklaşımı. LLM ve arama altyapısı bütçesi sebebiyle pilotta kullanılmadı. |
| https://github.com/HackerNews/API | MIT (dokümantasyon örnekleri) | Resmi HN API; RSS ile az çağrı tercih edildi. |

E-ticaret için ekran kazıma depoları ve lisansı belirsiz scraping araçları seçilmedi. Resmi Etsy API ve izinli satıcı CSV, Google Trends sinyalleri ile niş araştırması yapılabilir; tüm ticari kararlar veri/marka/telif kontrolüne bağlıdır. Daha kapsamlı e-ticaret açık kaynak kodu denetimi kalan iş.

## Gmail

Otomatik erişim yok. Uygulama için ayrı bülten posta kutusu tercih edilir: `radar-newsletters` etiketi, tam gönderen allowlist, yalnızca mesaj başlığı, izinli kaynak bağlantısı; diğer mesajlara, eklere ve kişisel içeriklere erişme. Gmail API OAuth `gmail.readonly` kısıtlı kapsamdır ve etiket filtrelemesi OAuth yetkisinin kendisini etiketle sınırlandırmaz. Ayrı posta kutusu + etiket + gönderen allowlist en az erişim hedefler. https://developers.google.com/workspace/gmail/api/auth/scopes ve https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list. Genel hesaptan veri çekmek, birleştirmek veya harici AI'ya aktarmak yok; bağlantı ayrı yetkilendirme ve koşul kontrolü gerektirir.
