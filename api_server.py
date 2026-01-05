"""
API Server Module.

This module initializes the Flask application, handles API routes for
crypto data, scraping, analysis, and historical data.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from core import BinanceTokensFetcher, CryptoAnalyzer, MessyWebScraper

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

api_fetcher = BinanceTokensFetcher(limit=50)
scraper = MessyWebScraper()
analyzer = CryptoAnalyzer()

@app.route('/api/live-data', methods=['GET'])
def get_live_data():
    """Live Binance Data + Anomaly Analysis"""
    try:
        raw_data = api_fetcher.fetch_data()
        processed_data = analyzer.detect_anomalies(raw_data)
        return jsonify([t.to_dict() for t in processed_data])
    except Exception as e:  # pylint: disable=broad-exception-caught
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraped-data', methods=['GET'])
def get_scraped():
    """Web Scraping Data + Regex Cleaning + Anomaly Analysis"""
    try:
        data = scraper.scrape_data()
        processed = analyzer.detect_anomalies(data)
        return jsonify([t.to_dict() for t in processed])
    except Exception as e:  # pylint: disable=broad-exception-caught
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Detailed Seaborn Statistical Report (including Heatmap)"""
    try:
        raw_data = api_fetcher.fetch_data()
        report = analyzer.get_advanced_analysis(raw_data)
        return jsonify(report)
    except Exception as e:  # pylint: disable=broad-exception-caught
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<symbol>', methods=['GET'])
def get_token_history(symbol):
    """
    Historical Data for Candlestick Chart.
    Reads 'interval' parameter (15m, 1h, 4h, 1d, 1w, 1M) from React.
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
    except Exception as e:  # pylint: disable=broad-exception-caught
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(">>> PYTHON SERVER RUNNING (Port: 5000)...")
    app.run(debug=True, port=5000)