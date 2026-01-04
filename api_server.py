# Dosya Adı: api_server.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from core import BinanceTokensFetcher, CryptoAnalyzer, MessyWebScraper

app = Flask(__name__)
# CORS: Tüm kaynaklara izin ver (Tarayıcı engellemelerini önler)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# LİMİTİ 50 OLARAK AYARLIYORUZ (Senin İsteğin)
api_fetcher = BinanceTokensFetcher(limit=50) 
scraper = MessyWebScraper()
analyzer = CryptoAnalyzer()

@app.route('/api/live-data', methods=['GET'])
def get_live_data():
    """Canlı Binance Verisi + Anomali Analizi"""
    try:
        raw_data = api_fetcher.fetch_data()
        processed_data = analyzer.detect_anomalies(raw_data)
        return jsonify([t.to_dict() for t in processed_data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraped-data', methods=['GET'])
def get_scraped():
    """Web Scraping Verisi + Regex Temizleme + Anomali Analizi"""
    try:
        data = scraper.scrape_data()
        processed = analyzer.detect_anomalies(data)
        return jsonify([t.to_dict() for t in processed])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Detaylı Seaborn İstatistik Raporu (Heatmap dahil)"""
    try:
        raw_data = api_fetcher.fetch_data()
        report = analyzer.get_advanced_analysis(raw_data)
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<symbol>', methods=['GET'])
def get_token_history(symbol):
    """
    Mum Grafiği İçin Tarihsel Veri.
    React'ten gelen 'interval' parametresini (15m, 1h, 4h, 1d, 1w, 1M) okur.
    """
    try:
        interval = request.args.get('interval', '1h')
        
        limit_map = {
            '15m': 96,
            '1h': 24,
            '4h': 30,
            '1d': 30,
            '1w': 52,
            '1M': 12
        }
        limit = limit_map.get(interval, 24)
        
        history = api_fetcher.fetch_historical_data(symbol, interval=interval, limit=limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(">>> PYTHON SERVER ÇALIŞIYOR (Port: 5000)...")
    app.run(debug=True, port=5000)
