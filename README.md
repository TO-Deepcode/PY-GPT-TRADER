# Atlas T7 Python Market Service

Bu dizin, mevcut Node.js tabanlı Vercel servisinin Python/FastAPI eşleniğidir. Bybit, Binance (spot + USDT-M futures), CoinMarketCap ve seçili haber akışlarından veri toplayarak `/api/market`, `/api/bybit`, `/api/binance`, `/api/cmc` ve `/api/news` uçlarını sunar.

## Hızlı Başlangıç

```bash
cd services/python_api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- Varsayılan olarak CORS tüm origin’lere açık bırakılmıştır (`ATLAS_CORS_ORIGINS` env değişkeni ile güncelleyebilirsiniz).
- CoinMarketCap uçları için `CMC_API_KEY` ortam değişkeni zorunludur.
- Bybit/Binance için özel host veya origin/Referer ayarlarını `.env` üzerinden yönlendirebilirsiniz (örn. `BYBIT_BASE_URL`, `BINANCE_FUTURES_HOSTS`).

## Vercel Deploy

Bu dizin Vercel’de tek Python serverless fonksiyonu olarak çalışacak şekilde yapılandırılmıştır.

1. `vercel.json` dosyası `runtime: python3.11` ile `api/index.py` fonksiyonunu hedefler.
2. Vercel projesinde gerekli ortam değişkenlerini tanımlayın (örn. `CMC_API_KEY`, `BYBIT_BASE_URL`, `BINANCE_FUTURES_HOSTS`).
3. Depoyu Vercel’e bağlayın ve kök olarak `services/python_api` dizinini seçin.
4. Vercel, `requirements.txt` dosyasını kullanarak bağımlılıkları kurar ve `api/index.py` dosyasındaki `handler = Mangum(app)` tanımıyla FastAPI uygulamasını çalıştırır.

> Yerel geliştirme yerine Vercel CLI ile test etmek için:
> ```bash
> vercel dev --listen 0.0.0.0:8000
> ```

Dağıtım sonrası `https://<vercel-domain>/api/market` gibi uçlar doğrudan kullanılabilir.

## Ortam Değişkenleri

| Değişken | Açıklama | Varsayılan |
| --- | --- | --- |
| `CMC_API_KEY` | CoinMarketCap Pro anahtarı (zorunlu) | — |
| `BYBIT_BASE_URL` | Bybit API hostu | `https://api.bybit.com` |
| `BYBIT_CATEGORY` | Bybit kategori parametresi | `linear` |
| `BINANCE_SPOT_HOSTS` | Virgülle ayrılmış spot host listesi | `https://api.binance.com,...` |
| `BINANCE_FUTURES_HOSTS` | Virgülle ayrılmış futures host listesi | `https://fapi.binance.com,...` |
| `ATLAS_HTTP_TIMEOUT` | HTTP timeout (saniye) | `8` |
| `ATLAS_USER_AGENT` | HTTP User-Agent | `Atlas-T7-Python/1.0` |
| `ATLAS_CORS_ORIGINS` | CORS origin listesi | `*` |

## Uçlar

- `GET /api/market`: Bybit + Binance + CMC birleşik çıktı.
- `GET /api/bybit`: Bybit klines/orderbook/trades.
- `GET /api/binance`: Binance spot/futures klines/orderbook/trades.
- `GET /api/cmc`: CMC quotes veya global metrics.
- `GET /api/news`: CoinDesk, The Block vb. RSS kaynakları.

Node.js sürümünde olduğu gibi, eksik veri durumunda HTTP 207 (partial) yanıtı döndürülür; haberler feedparser ile parse edilir.

## Production Deploy

- `uvicorn main:app` komutu ile WSGI sunucusu olarak çalıştırın veya FastAPI uyumlu bir ortamda (vercel, fly.io, docker) deploy edin.
- Sürekli çağrılarda rate limit’e takılmamak için TTL/cache mekanizmaları ekleyebilirsiniz.
