"""
Core processing module for the Crypto Analytics System.
Contains data structures, mathematical engines, scraping logic,
and analysis tools.
"""
import re
import io
import base64
import time
import random
from typing import List, Dict, Any
import requests
import pandas as pd
from bs4 import BeautifulSoup
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

matplotlib.use('Agg')

class TokenData:
    """
    Data carrier class.
    """
    # pylint: disable=too-many-instance-attributes, too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def __init__(self, token_id, symbol, name, current_price,
                 price_change_percentage_24h, market_cap_rank):
        self.id = token_id  # pylint: disable=invalid-name
        self.symbol = symbol
        self.name = name
        self.current_price = current_price
        self.market_cap_rank = market_cap_rank
        self.price_change_percentage_24h = price_change_percentage_24h
        self.is_anomaly = False
        self.anomaly_score = 0.0

    def to_dict(self):
        """Converts class data into a JSON-serializable dictionary."""
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

class MathEngine:
    """
    A manual statistics engine.
    """
    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """Mean calculation algorithm."""
        if not values:
            return 0.0
        total = sum(values)
        count = len(values)
        return total / count

    @staticmethod
    def calculate_variance(values: List[float], mean: float) -> float:
        """Variance calculation (loop-based)."""
        if not values or len(values) < 2:
            return 0.0
        sum_sq_diff = 0.0
        for x in values:
            sum_sq_diff += (x - mean) ** 2
        return sum_sq_diff / len(values)

    @staticmethod
    def calculate_std_dev(values: List[float], mean: float) -> float:
        """Standard deviation calculation."""
        variance = MathEngine.calculate_variance(values, mean)
        return variance ** 0.5

    @staticmethod
    def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
        """Z-score calculation."""
        if std_dev == 0:
            return 0.0
        return (value - mean) / std_dev

class PredictionEngine:
    """
    A simple price prediction engine using linear regression.
    """
    @staticmethod
    def linear_regression_predict(prices: List[float]) -> float:
        """
        Predicts the next price using Least Squares linear regression.
        """
        if not prices or len(prices) < 2:
            return 0.0

        n = len(prices)
        x_vals = list(range(n))
        y_vals = prices

        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        # pylint: disable=consider-using-generator
        sum_xy = sum([xi * yi for xi, yi in zip(x_vals, y_vals)])
        sum_xx = sum([xi ** 2 for xi in x_vals])

        denominator = (n * sum_xx - sum_x ** 2)
        if denominator == 0:
            return y_vals[-1]

        m = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - m * sum_x) / n

        next_price = m * n + b
        return next_price

class SentimentEngine:
    """
    A simple rule-based sentiment engine.
    """
    @staticmethod
    def analyze_market_sentiment(tokens: List[TokenData]) -> Dict[str, Any]:
        """Analyzes market sentiment."""
        bullish_count = 0
        bearish_count = 0
        total_change = 0.0

        for t in tokens:
            change = t.price_change_percentage_24h
            total_change += change
            if change > 0:
                bullish_count += 1
            else:
                bearish_count += 1

        total_tokens = len(tokens) if tokens else 1
        sentiment_score = (bullish_count - bearish_count) / total_tokens

        status = "NEUTRAL"
        if sentiment_score > 0.15:
            status = "STRONG BUY (Bullish)"
        elif sentiment_score < -0.15:
            status = "STRONG SELL (Bearish)"

        return {
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "average_market_change": total_change / total_tokens,
            "sentiment_score": round(sentiment_score, 2),
            "market_status": status
        }

class MessyWebScraper:
    """Scrapes crypto data from web sources."""
    def __init__(self):
        self.url = "https://coinranking.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        }

    def _advanced_clean_currency(self, raw_value: str) -> float:
        """Regex-based cleaning for messy numeric strings."""
        if not raw_value:
            return 0.0

        clean_str = raw_value.lower().strip()
        clean_str = clean_str.replace("$", "").replace(",", "")

        multiplier = 1.0
        if "trillion" in clean_str:
            multiplier = 1_000_000_000_000
            clean_str = clean_str.replace("trillion", "")
        elif "billion" in clean_str:
            multiplier = 1_000_000_000
            clean_str = clean_str.replace("billion", "")
        elif "million" in clean_str:
            multiplier = 1_000_000
            clean_str = clean_str.replace("million", "")

        match = re.search(r"(-?\d+(\.\d+)?)", clean_str)
        if match:
            try:
                numeric_val = float(match.group(1))
                return numeric_val * multiplier
            except ValueError:
                return 0.0
        return 0.0

    def scrape_data(self) -> List[TokenData]:
        """Main scraping method."""
        print(">>> Web Scraping (Coinranking) started...")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.find_all("tr", class_="table__row")
            tokens = []

            for index, row in enumerate(rows[:50]):
                try:
                    name = row.find("span", class_="profile__name").text.strip()
                    symbol = row.find("span", class_="profile__subtitle").text.strip()
                    price_raw = row.find("div", class_="valuta--light").text
                    change_raw = row.find("div", class_="change").text

                    clean_price = self._advanced_clean_currency(price_raw)
                    clean_change = self._advanced_clean_currency(
                        change_raw.replace("%", "")
                    )
                    clean_change = clean_change if isinstance(
                        clean_change, (int, float)
                    ) else 0.0

                    t = TokenData(
                        token_id=symbol,
                        symbol=symbol,
                        name=name,
                        current_price=clean_price,
                        price_change_percentage_24h=clean_change,
                        market_cap_rank=index + 1
                    )
                    tokens.append(t)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue

            if not tokens:
                # pylint: disable=broad-exception-raised
                raise Exception("Scraping returned empty data.")
            return tokens

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"!!! Scraping error: {e}")
            return self._generate_fallback_data()

    def _generate_fallback_data(self):
        """Generates fallback token rows."""
        data = []
        leaders = [
            ("BTC", "Bitcoin", 94500.0), ("ETH", "Ethereum", 3100.0),
            ("BNB", "Binance Coin", 620.0), ("SOL", "Solana", 145.0),
            ("XRP", "Ripple", 2.40), ("ADA", "Cardano", 0.75),
            ("DOGE", "Dogecoin", 0.18), ("AVAX", "Avalanche", 45.0),
            ("DOT", "Polkadot", 8.5), ("TRX", "Tron", 0.14),
            ("LINK", "Chainlink", 18.0), ("MATIC", "Polygon", 0.95),
            ("SHIB", "Shiba Inu", 0.000025), ("LTC", "Litecoin", 88.0),
            ("UNI", "Uniswap", 11.5), ("ATOM", "Cosmos", 10.0),
            ("XLM", "Stellar", 0.35), ("ETC", "Ethereum Classic", 25.0),
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

            data.append(TokenData(sym, sym, name, price, change, i + 1))
        return data

class BinanceTokensFetcher:
    """Fetches data from Binance API."""
    def __init__(self, limit: int = 50):
        self.limit = limit
        self.base_url = "https://api.binance.com/api/v3"
        self._last_good_tokens: List[TokenData] = []
        self._last_fetch_time: float = 0.0
        self._cache_ttl_seconds: float = 1.2
        self._max_retry: int = 3

    def fetch_data(self) -> List[TokenData]:
        """Main fetch method."""
        try:
            now_time = time.time()
            if self._last_good_tokens and \
               (now_time - self._last_fetch_time) < self._cache_ttl_seconds:
                return self._last_good_tokens

            last_exc = None
            r_data = None
            for attempt in range(self._max_retry):
                try:
                    resp = requests.get(f"{self.base_url}/ticker/24hr", timeout=5)
                    if hasattr(resp, "status_code") and resp.status_code != 200:
                        # pylint: disable=broad-exception-raised
                        raise Exception(f"HTTP Error: {resp.status_code}")

                    r_data = resp.json()
                    if isinstance(r_data, dict) and "code" in r_data:
                        # pylint: disable=broad-exception-raised
                        raise Exception("Binance API Error")

                    last_exc = None
                    break
                except Exception as e:  # pylint: disable=broad-exception-caught
                    last_exc = e
                    time.sleep(0.08 * (attempt + 1))

            if last_exc is not None:
                # pylint: disable=raising-bad-type
                raise last_exc

            usdt_pairs = [x for x in r_data if x["symbol"].endswith("USDT")]
            usdt_pairs.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)

            tokens = []
            for i, item in enumerate(usdt_pairs[:self.limit]):
                try:
                    pct_str = item.get("priceChangePercent", 0)
                    pct_val = float(pct_str) if pct_str not in [None, "", "nan", "NaN"] else 0.0

                    t = TokenData(
                        token_id=item["symbol"],
                        symbol=item["symbol"].replace("USDT", ""),
                        name=item["symbol"],
                        current_price=float(item["lastPrice"]),
                        price_change_percentage_24h=pct_val,
                        market_cap_rank=i + 1
                    )
                    tokens.append(t)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue

            if not tokens:
                # pylint: disable=broad-exception-raised
                raise Exception("API returned empty data.")

            self._last_good_tokens = tokens
            self._last_fetch_time = time.time()

            return tokens

        except Exception as e:  # pylint: disable=broad-exception-caught
            if self._last_good_tokens and len(self._last_good_tokens) > 0:
                print(f"!!! Binance temporary issue, returning cached data. Error: {e}")
                return self._last_good_tokens
            # pylint: disable=protected-access
            return MessyWebScraper()._generate_fallback_data()

    def fetch_historical_data(self, symbol: str, interval: str = "1h",
                              limit: int = 24) -> List[Dict]:
        """
        Fetches candlestick (OHLC) data for charting.
        """
        try:
            url = f"{self.base_url}/klines"
            params = {"symbol": f"{symbol.upper()}USDT",
                      "interval": interval, "limit": limit}
            r_data = requests.get(url, params=params, timeout=5).json()

            if isinstance(r_data, dict) and "code" in r_data:
                # pylint: disable=broad-exception-raised
                raise Exception("Symbol Not Found")

            formatted = []
            for item in r_data:
                formatted.append({
                    "x": int(item[0]),
                    "y": [float(item[1]), float(item[2]), float(item[3]), float(item[4])]
                })
            return formatted
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Historical data unavailable for ({symbol}), using simulation fallback. "
                  f"Error: {e}")

            now = int(time.time() * 1000)
            mock_data = []
            price = 100.0

            time_steps = {
                "15m": 900000,
                "1h": 3600000,
                "4h": 14400000,
                "1d": 86400000,
                "1w": 604800000,
                "1M": 2592000000
            }
            step_ms = time_steps.get(interval, 3600000)

            for i in range(limit):
                open_p = price
                change = random.uniform(0.98, 1.02)
                close_p = open_p * change
                high_p = max(open_p, close_p) * random.uniform(1.001, 1.01)
                low_p = min(open_p, close_p) * random.uniform(0.99, 0.999)

                mock_data.append({
                    "x": now - ((limit - i) * step_ms),
                    "y": [open_p, high_p, low_p, close_p]
                })

                price = close_p

            return mock_data

class CryptoAnalyzer:
    """Analyzes crypto data for anomalies and statistics."""
    def detect_anomalies(self, data: List[TokenData]) -> List[TokenData]:
        """Detects anomalies using MathEngine (manual algorithm)."""
        if not data:
            return []
        prices = [t.current_price for t in data]

        mean = MathEngine.calculate_mean(prices)
        std_dev = MathEngine.calculate_std_dev(prices, mean)

        for t in data:
            if std_dev == 0:
                continue
            z_score = MathEngine.calculate_z_score(t.current_price, mean, std_dev)
            t.anomaly_score = z_score
            if abs(z_score) > 1.5:
                t.is_anomaly = True
        return data

    def get_advanced_analysis(self, data: List[TokenData]) -> Dict[str, Any]:
        """Generates advanced statistical report."""
        if not data:
            return {}
        try:
            # pylint: disable=too-many-locals
            df_frame = pd.DataFrame([t.to_dict() for t in data])
            col = "current_price"

            q1 = df_frame[col].quantile(0.25)
            q3 = df_frame[col].quantile(0.75)
            iqr = q3 - q1
            outliers = df_frame[
                (df_frame[col] < (q1 - 1.5 * iqr)) |
                (df_frame[col] > (q3 + 1.5 * iqr))
            ]

            skewness = df_frame[col].skew()
            kurtosis = df_frame[col].kurt()

            prices_for_pred = df_frame[col].head(20).tolist()
            predicted_price = PredictionEngine.linear_regression_predict(prices_for_pred)

            prediction_data = {
                "target_coin": data[0].symbol if data else "UNKNOWN",
                "current": data[0].current_price if data else 0,
                "predicted_next": round(predicted_price, 2),
                "trend": "UP" if predicted_price > (data[0].current_price if data else 0)
                else "DOWN"
            }

            sentiment_data = SentimentEngine.analyze_market_sentiment(data)

            plt.figure(figsize=(10, 5))
            sns.set_theme(style="darkgrid")
            sns.boxplot(x=df_frame[col], color="#00d1b2",
                        flierprops={"marker": "x", "markeredgecolor": "red"})
            plt.title("Price Distribution (Box Plot)")
            plt.tight_layout()

            img_bytes = io.BytesIO()
            plt.savefig(img_bytes, format="png")
            img_bytes.seek(0)
            box_plot = base64.b64encode(img_bytes.read()).decode("utf-8")
            plt.close()

            plt.figure(figsize=(8, 6))
            corr_cols = df_frame[["current_price",
                                  "price_change_percentage_24h",
                                  "market_cap_rank"]]

            corr_df = corr_cols.corr().round(6)
            corr_matrix = {k: {kk: float(vv) for kk, vv in v.items()}
                           for k, v in corr_df.to_dict().items()}

            raw_for_frontend = {
                "current_price":
                    [float(x) for x in df_frame["current_price"].fillna(0).tolist()],
                "price_change_percentage_24h":
                    [float(x) for x in df_frame["price_change_percentage_24h"]
                     .fillna(0).tolist()],
                "market_cap_rank":
                    [int(x) for x in df_frame["market_cap_rank"].fillna(0).tolist()],
                "symbols":
                    [str(x) for x in df_frame["symbol"].fillna("").tolist()],
                "names":
                    [str(x) for x in df_frame["name"].fillna("").tolist()],
                "is_anomaly":
                    [bool(x) for x in df_frame["is_anomaly"].fillna(False).tolist()],
                "anomaly_score":
                    [float(x) for x in df_frame["anomaly_score"].fillna(0).tolist()],
            }

            outliers_list = outliers[[
                "symbol", "name", "current_price",
                "price_change_percentage_24h", "market_cap_rank"
            ]].to_dict(orient="records")

            sns.heatmap(corr_cols.corr(), annot=True, cmap="coolwarm", fmt=".2f")
            plt.title("Correlation Matrix (Scientific Report)")
            plt.tight_layout()

            img_bytes_hm = io.BytesIO()
            plt.savefig(img_bytes_hm, format="png")
            img_bytes_hm.seek(0)
            heatmap = base64.b64encode(img_bytes_hm.read()).decode("utf-8")
            plt.close()

            return {
                "stats": {
                    "q1": round(q1, 2),
                    "q3": round(q3, 2),
                    "iqr": round(iqr, 2),
                    "outliers_count": len(outliers),
                    "mean": round(df_frame[col].mean(), 2),
                    "skewness": round(skewness, 2),
                    "kurtosis": round(kurtosis, 2)
                },
                "prediction": prediction_data,
                "sentiment": sentiment_data,
                "plot_image": f"data:image/png;base64,{box_plot}",
                "heatmap_image": f"data:image/png;base64,{heatmap}",
                "corr_matrix": corr_matrix,
                "raw": raw_for_frontend,
                "outliers": outliers_list
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Analysis error: {e}")
            return {}