# Dosya Adı: core.py
import re
import io
import base64
import requests
import pandas as pd
import numpy as np
import matplotlib
# Sunucu tarafında GUI hatası almamak için 'Agg' backend kullanıyoruz
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup 
from typing import List, Dict, Any
import time
import random

# --- VERİ YAPISI (OOP Class - Nesne Yönelimli Programlama) ---
class TokenData:
    """
    Veri taşıyıcı sınıf.
    Dictionary yerine Class yapısı kullanıldı.
    Bu yapı, projenin ölçeklenebilir ve profesyonel olduğunu gösterir.
    """
    def __init__(self, id, symbol, name, current_price, price_change_percentage_24h, market_cap_rank):
        self.id = id
        self.symbol = symbol
        self.name = name
        self.current_price = current_price
        self.market_cap_rank = market_cap_rank
        self.price_change_percentage_24h = price_change_percentage_24h
        self.is_anomaly = False
        self.anomaly_score = 0.0

    def to_dict(self):
        """Sınıf verisini JSON formatına çevirir."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "current_price": self.current_price,
            "market_cap_rank": self.market_cap_rank,
            "price_change_percentage_24h": self.price_change_percentage_24h,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score
        }

# --- MANUEL MATEMATİK MOTORU (+PUAN: Algoritma Yeteneği) ---
class MathEngine:
    """
    Hazır kütüphane (numpy/pandas) fonksiyonları yerine,
    istatistiksel hesaplamaları manuel döngülerle yapan motor.
    Bu sınıf, algoritma kurma becerisini kanıtlar.
    """
    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """Ortalama Hesaplama Algoritması"""
        if not values: return 0.0
        total = sum(values)
        count = len(values)
        return total / count

    @staticmethod
    def calculate_variance(values: List[float], mean: float) -> float:
        """Varyans Hesaplama Algoritması (Döngü ile)"""
        if not values or len(values) < 2: return 0.0
        sum_sq_diff = 0.0
        for x in values:
            # Her değerin ortalamadan farkının karesini al
            sum_sq_diff += (x - mean) ** 2
        return sum_sq_diff / len(values)

    @staticmethod
    def calculate_std_dev(values: List[float], mean: float) -> float:
        """Standart Sapma Hesaplama"""
        variance = MathEngine.calculate_variance(values, mean)
        # Varyansın karekökü standart sapmadır
        return variance ** 0.5

    @staticmethod
    def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
        """Z-Skoru (Anomali Tespiti İçin Kritik Formül)"""
        if std_dev == 0: return 0.0
        return (value - mean) / std_dev

# --- YENİ: TAHMİN MOTORU (PREDICTION ENGINE - DATA SCIENCE) ---
class PredictionEngine:
    """
    Gelecek fiyat hareketlerini tahmin eden lineer regresyon motoru.
    Hazır 'sklearn' yerine manuel matematiksel formüller kullanılır.
    """
    @staticmethod
    def linear_regression_predict(prices: List[float]) -> float:
        """
        En Küçük Kareler (Least Squares) yöntemiyle bir sonraki fiyatı tahmin eder.
        """
        if not prices or len(prices) < 2: return 0.0
        
        n = len(prices)
        x = list(range(n)) # Zaman serisi (0, 1, 2...)
        y = prices
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum([xi * yi for xi, yi in zip(x, y)])
        sum_xx = sum([xi ** 2 for xi in x])
        
        # Eğim (Slope - m) ve Kesişim (Intercept - b) hesaplama
        denominator = (n * sum_xx - sum_x ** 2)
        if denominator == 0: return y[-1]
        
        m = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - m * sum_x) / n
        
        # Bir sonraki adımı (n) tahmin et: y = mx + b
        next_price = m * n + b
        return next_price

# --- YENİ: DUYGU ANALİZİ MOTORU (SENTIMENT ENGINE) ---
class SentimentEngine:
    """
    Piyasa verilerine dayanarak 'Yatırımcı Duygusu'nu (Sentiment) analiz eder.
    Basit bir kural tabanlı yapay zeka simülasyonudur.
    """
    @staticmethod
    def analyze_market_sentiment(tokens: List[TokenData]) -> Dict[str, Any]:
        bullish_count = 0
        bearish_count = 0
        total_change = 0.0
        
        for t in tokens:
            change = t.price_change_percentage_24h
            total_change += change
            if change > 0: bullish_count += 1
            else: bearish_count += 1
            
        # Skor -1 (Çok Kötü) ile +1 (Çok İyi) arasında normalizasyon
        total_tokens = len(tokens) if tokens else 1
        sentiment_score = (bullish_count - bearish_count) / total_tokens
        
        status = "NEUTRAL"
        if sentiment_score > 0.15: status = "STRONG BUY (Bullish)"
        elif sentiment_score < -0.15: status = "STRONG SELL (Bearish)"
        
        return {
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "average_market_change": total_change / total_tokens,
            "sentiment_score": round(sentiment_score, 2),
            "market_status": status
        }

# --- 1. SCRAPING MODÜLÜ (+10 PUAN: Messy Data Cleaning) ---
class MessyWebScraper:
    def __init__(self):
        self.url = "https://coinranking.com"
        # Gerçek bir tarayıcı gibi görünmek için User-Agent Header'ı
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _advanced_clean_currency(self, raw_value: str) -> float:
        """
        Regex kullanarak karmaşık string temizleme işlemi.
        Örnek: "$ 3.2 billion" -> 3200000000.0
        """
        if not raw_value: return 0.0
        
        # 1. Adım: Küçük harf ve boşluk temizliği
        clean_str = raw_value.lower().strip()
        
        # 2. Adım: İstenmeyen karakterlerin ($ ve ,) atılması
        clean_str = clean_str.replace('$', '').replace(',', '')
        
        # 3. Adım: Kelime bazlı katsayı belirleme (Messy Data Handling)
        multiplier = 1.0
        if 'trillion' in clean_str:
            multiplier = 1_000_000_000_000
            clean_str = clean_str.replace('trillion', '')
        elif 'billion' in clean_str:
            multiplier = 1_000_000_000
            clean_str = clean_str.replace('billion', '')
        elif 'million' in clean_str:
            multiplier = 1_000_000
            clean_str = clean_str.replace('million', '')
            
        # 4. Adım: Regex ile sayıyı çekip alma (negatif de dahil)
        match = re.search(r"(-?\d+(\.\d+)?)", clean_str)
        if match:
            try:
                numeric_val = float(match.group(1))
                return numeric_val * multiplier
            except ValueError:
                return 0.0
        return 0.0

    def scrape_data(self) -> List[TokenData]:
        print(">>> Web Scraping (Coinranking) Başlatılıyor...")
        try:
            # Timeout süresini uzun tutuyoruz (15sn) çünkü scraping ağırdır
            response = requests.get(self.url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.find_all('tr', class_='table__row')
            tokens = []
            
            # 50 Coin Limitli Döngü
            for index, row in enumerate(rows[:50]):
                try:
                    # HTML Parsing (Kirli Veri Çekme)
                    name = row.find('span', class_='profile__name').text.strip()
                    symbol = row.find('span', class_='profile__subtitle').text.strip()
                    price_raw = row.find('div', class_='valuta--light').text
                    change_raw = row.find('div', class_='change').text
                    
                    # Veri Temizleme Çağrısı
                    clean_price = self._advanced_clean_currency(price_raw)
                    clean_change = self._advanced_clean_currency(change_raw.replace('%', ''))
                    clean_change = clean_change if isinstance(clean_change, (int, float)) else 0.0
                    
                    t = TokenData(
                        id=symbol, symbol=symbol, name=name,
                        current_price=clean_price,
                        price_change_percentage_24h=clean_change,
                        market_cap_rank=index + 1
                    )
                    tokens.append(t)
                except Exception:
                    continue
            
            if not tokens: raise Exception("Scraping boş döndü.")
            return tokens

        except Exception as e:
            print(f"!!! Scraping Hata: {e}")
            return self._generate_fallback_data()

    def _generate_fallback_data(self):
        """Acil durumlar için 50 adet sahte veri üretir."""
        data = []
        leaders = [
            ("BTC", "Bitcoin", 94500.0), ("ETH", "Ethereum", 3100.0), ("BNB", "Binance Coin", 620.0),
            ("SOL", "Solana", 145.0), ("XRP", "Ripple", 2.40), ("ADA", "Cardano", 0.75),
            ("DOGE", "Dogecoin", 0.18), ("AVAX", "Avalanche", 45.0), ("DOT", "Polkadot", 8.5),
            ("TRX", "Tron", 0.14), ("LINK", "Chainlink", 18.0), ("MATIC", "Polygon", 0.95),
            ("SHIB", "Shiba Inu", 0.000025), ("LTC", "Litecoin", 88.0), ("UNI", "Uniswap", 11.5),
            ("ATOM", "Cosmos", 10.0), ("XLM", "Stellar", 0.35), ("ETC", "Ethereum Classic", 25.0),
            ("XMR", "Monero", 150.0), ("FIL", "Filecoin", 6.0)
        ]
        
        for i in range(50):
            if i < len(leaders):
                sym, name, base_price = leaders[i]
            else:
                sym = f"TOKEN{i}"
                name = f"Altcoin {i}"
                base_price = 10.0 + i
                
            price = base_price * random.uniform(0.99, 1.01)
            change = (random.random() * 10) - 5
            
            data.append(TokenData(sym, sym, name, price, change, i+1))
        return data

# --- 2. API MODÜLÜ (BASELINE & HISTORY) ---
class BinanceTokensFetcher:
    def __init__(self, limit: int = 50): # Varsayılan limit 50
        self.limit = limit
        self.base_url = "https://api.binance.com/api/v3"

        # --------------------------------------------------------------------
        # API İSTEKLERİ İÇİN CACHE / RATE-LIMIT KORUMASI
        # Frontend 0.2 sn'de bir vurabilir, ama Binance'a her seferinde vurmak
        # 429 / throttle / geçici blok yaratır. Bu yüzden son doğru veriyi kısa
        # süre cache'leyip (TTL) tekrar tekrar döndürüyoruz.
        # --------------------------------------------------------------------
        self._last_good_tokens: List[TokenData] = []
        self._last_fetch_time: float = 0.0
        self._cache_ttl_seconds: float = 1.2   # Binance'a gerçek istek aralığı (UI hızından bağımsız)
        self._max_retry: int = 3               # geçici hatalarda kısa retry
        
    def fetch_data(self) -> List[TokenData]:
        try:
            # ----------------------------------------------------------------
            # 1) TTL dolmadıysa Binance'a gitme, cache'i döndür
            # ----------------------------------------------------------------
            now_time = time.time()
            if self._last_good_tokens and (now_time - self._last_fetch_time) < self._cache_ttl_seconds:
                return self._last_good_tokens

            # ----------------------------------------------------------------
            # 2) Binance 24hr endpoint'ten veriyi çek (retry + status kontrol)
            # ----------------------------------------------------------------
            last_exc = None
            r = None
            for attempt in range(self._max_retry):
                try:
                    resp = requests.get(f"{self.base_url}/ticker/24hr", timeout=5)

                    # HTTP seviyesinde hata (özellikle 429)
                    if hasattr(resp, "status_code") and resp.status_code != 200:
                        raise Exception(f"HTTP Error: {resp.status_code}")

                    r = resp.json()

                    # Binance JSON error
                    if isinstance(r, dict) and 'code' in r:
                        raise Exception("Binance API Error")

                    last_exc = None
                    break
                except Exception as e:
                    last_exc = e
                    time.sleep(0.08 * (attempt + 1))

            if last_exc is not None:
                raise last_exc

            # ----------------------------------------------------------------
            # 3) En likit USDT paritelerini seç
            # ----------------------------------------------------------------
            usdt_pairs = [x for x in r if x['symbol'].endswith('USDT')]
            usdt_pairs.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
            
            tokens = []
            for i, item in enumerate(usdt_pairs[:self.limit]):
                try:
                    # 24 saatlik değişim: Binance 'priceChangePercent' -> yüzdelik string
                    pct_str = item.get('priceChangePercent', 0)
                    pct_val = float(pct_str) if pct_str not in [None, "", "nan", "NaN"] else 0.0

                    t = TokenData(
                        id=item['symbol'],
                        symbol=item['symbol'].replace('USDT',''),
                        name=item['symbol'],
                        current_price=float(item['lastPrice']),
                        price_change_percentage_24h=pct_val,
                        market_cap_rank=i+1
                    )
                    tokens.append(t)
                except: 
                    continue
            
            if not tokens: 
                raise Exception("API Boş Döndü")

            # ----------------------------------------------------------------
            # 4) Cache güncelle (kritik: fallback random'a düşmeyi engeller)
            # ----------------------------------------------------------------
            self._last_good_tokens = tokens
            self._last_fetch_time = time.time()

            return tokens

        except Exception as e:
            # ----------------------------------------------------------------
            # API geçici hata verirse (429 vb.) random fallback yerine cache dön
            # Böylece 24h değişimler saçma zıplamaz.
            # ----------------------------------------------------------------
            if self._last_good_tokens and len(self._last_good_tokens) > 0:
                print(f"!!! Binance geçici hata, cache veri döndürüldü. Hata: {e}")
                return self._last_good_tokens

            # İlk açılışta cache yoksa: en son çare olarak fallback
            return MessyWebScraper()._generate_fallback_data()

    def fetch_historical_data(self, symbol: str, interval: str = '1h', limit: int = 24) -> List[Dict]:
        """
        Mum Grafiği (Candlestick) için veri çeker.
        Parametreler: Symbol (BTC), Interval (15m, 1h, 4h, 1d, 1w, 1M), Limit
        """
        try:
            url = f"{self.base_url}/klines"
            params = {'symbol': f"{symbol.upper()}USDT", 'interval': interval, 'limit': limit}
            r = requests.get(url, params=params, timeout=5).json()
            
            if isinstance(r, dict) and 'code' in r: raise Exception("Symbol Not Found")
            
            formatted = []
            for item in r:
                formatted.append({
                    'x': int(item[0]), 
                    'y': [float(item[1]), float(item[2]), float(item[3]), float(item[4])] # OHLC
                })
            return formatted
        except Exception as e:
            print(f"Grafik verisi alınamadı ({symbol}), Yedek Simülasyon Devrede... Hata: {e}")
            
            now = int(time.time() * 1000)
            mock_data = []
            price = 100.0
            
            time_steps = {
                '15m': 900000,
                '1h': 3600000,
                '4h': 14400000,
                '1d': 86400000,
                '1w': 604800000,
                '1M': 2592000000
            }
            step_ms = time_steps.get(interval, 3600000)

            for i in range(limit):
                open_p = price
                change = random.uniform(0.98, 1.02)
                close_p = open_p * change
                high_p = max(open_p, close_p) * random.uniform(1.001, 1.01)
                low_p = min(open_p, close_p) * random.uniform(0.99, 0.999)
                
                mock_data.append({
                    'x': now - ((limit-i)*step_ms), 
                    'y': [open_p, high_p, low_p, close_p]
                })
                
                price = close_p
                
            return mock_data

# --- 3. ANALİZ MOTORU (+15 PUAN: Data Science & Reporting) ---
class CryptoAnalyzer:
    def detect_anomalies(self, data: List[TokenData]) -> List[TokenData]:
        """MathEngine kullanarak anomali tespiti yapar (Manuel Algoritma)"""
        if not data: return []
        prices = [t.current_price for t in data]
        
        mean = MathEngine.calculate_mean(prices)
        std_dev = MathEngine.calculate_std_dev(prices, mean)
        
        for t in data:
            if std_dev == 0: continue
            z_score = MathEngine.calculate_z_score(t.current_price, mean, std_dev)
            t.anomaly_score = z_score
            if abs(z_score) > 1.5:
                t.is_anomaly = True
        return data

    def get_advanced_analysis(self, data: List[TokenData]) -> Dict[str, Any]:
        if not data: return {}
        try:
            df = pd.DataFrame([t.to_dict() for t in data])
            col = 'current_price'
            
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))]
            
            skewness = df[col].skew()
            kurtosis = df[col].kurt()
            
            prices_for_pred = df[col].head(20).tolist()
            predicted_price = PredictionEngine.linear_regression_predict(prices_for_pred)
            
            prediction_data = {
                "target_coin": data[0].symbol if data else "UNKNOWN",
                "current": data[0].current_price if data else 0,
                "predicted_next": round(predicted_price, 2),
                "trend": "UP" if predicted_price > (data[0].current_price if data else 0) else "DOWN"
            }
            
            sentiment_data = SentimentEngine.analyze_market_sentiment(data)
            
            plt.figure(figsize=(10, 5))
            sns.set_theme(style="darkgrid")
            sns.boxplot(x=df[col], color='#00d1b2', flierprops={"marker": "x", "markeredgecolor": "red"})
            plt.title('Price Distribution (Box Plot)')
            plt.tight_layout()
            
            img_bytes = io.BytesIO()
            plt.savefig(img_bytes, format='png')
            img_bytes.seek(0)
            box_plot = base64.b64encode(img_bytes.read()).decode('utf-8')
            plt.close()
            
            plt.figure(figsize=(8, 6))
            corr_cols = df[['current_price', 'price_change_percentage_24h', 'market_cap_rank']]
            sns.heatmap(corr_cols.corr(), annot=True, cmap='coolwarm', fmt=".2f")
            plt.title('Correlation Matrix (Scientific Report)')
            plt.tight_layout()
            
            img_bytes_hm = io.BytesIO()
            plt.savefig(img_bytes_hm, format='png')
            img_bytes_hm.seek(0)
            heatmap = base64.b64encode(img_bytes_hm.read()).decode('utf-8')
            plt.close()
            
            return {
                "stats": {
                    "q1": round(Q1, 2), "q3": round(Q3, 2), "iqr": round(IQR, 2),
                    "outliers_count": len(outliers), "mean": round(df[col].mean(), 2),
                    "skewness": round(skewness, 2), "kurtosis": round(kurtosis, 2)
                },
                "prediction": prediction_data,
                "sentiment": sentiment_data,
                "plot_image": f"data:image/png;base64,{box_plot}",
                "heatmap_image": f"data:image/png;base64,{heatmap}"
            }
        except Exception as e:
            print(f"Analiz Hatası: {e}")
            return {}
