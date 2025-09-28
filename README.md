# Atlas T7 FastAPI Service (Vercel Şablonu)

Bu klasör, Vercel üzerinde serverless olarak çalışacak FastAPI servisi için hazır şablondur. İçeriği **aynen depo köküne** (GitHub repo root) koyup Vercel’e bağladığınızda gerçek zamanlı Bybit/Binance/CoinMarketCap verilerini servis edecek `/api/*` uçları elde edersiniz.

## Dosya Yapısı
```
.
├── api/
│   └── index.py            # Vercel serverless giriş noktası (Mangum)
├── clients/
│   ├── __init__.py
│   ├── bybit.py            # Bybit v5 helper
│   ├── binance.py          # Binance spot + futures helper
│   ├── coinmarketcap.py    # CMC helper
│   └── http.py             # Ortak HTTP wrapper
├── news/
│   ├── __init__.py
│   ├── aggregator.py       # RSS toplama mantığı
│   └── sources.py          # Haber kaynak listesi
├── main.py                 # FastAPI uygulaması ve endpoint’ler
├── requirements.txt        # Bağımlılıklar
└── vercel.json             # Vercel Python runtime ayarı
```

## Vercel Kurulumu
1. Bu klasör içeriğini yeni GitHub deposunun köküne kopyala.
2. Vercel’e bağlarken aşağıdaki ayarları kullan:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: boş bırak (None)
   - **Install Command**: `pip install -r requirements.txt`
   - **Output Directory**: boş bırak
3. Aşağıdaki ortam değişkenlerini Vercel panelinde tanımla:
   - `CMC_API_KEY` *(zorunlu)*
   - `BYBIT_BASE_URL`, `BYBIT_CATEGORY` *(opsiyonel, varsayılan prod host)*
   - `BINANCE_SPOT_HOSTS`, `BINANCE_FUTURES_HOSTS` *(opsiyonel, varsayılan prod host)*
   - `ATLAS_USER_AGENT`, `ATLAS_HTTP_TIMEOUT` vb. opsiyonel ayarlar
4. Deploy sonrası `https://<project>.vercel.app/api/market?symbol=BTCUSDT&interval=1h` gibi uçları çağırarak canlı veriyi doğrula.

## Yerel Çalıştırma (opsiyonel)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Bu şekilde FastAPI uygulamasını yerelde test edebilir, ardından Vercel’e push ettiğinde aynı kod serverless fonksiyon olarak çalışır.
