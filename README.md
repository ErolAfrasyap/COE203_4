# 📈 Crypto Analytics & Prediction Engine

A full-stack cryptocurrency analysis platform combining real-time API data, web scraping, and custom statistical algorithms.

This system aggregates market data, detects price anomalies using Z-Score analysis, and visualizes trends via server-side rendered heatmaps and box plots. It features a **Python Flask** backend serving a **React** frontend.

## ⚡ Key Features

* **Hybrid Data Architecture:**

    * **Live:** Real-time data fetching from **Binance API**.

    * **Scraper:** Custom `BeautifulSoup` scraper with Regex cleaning for unstructured data sources (Coinranking).

* **Custom Math Engine:** Core statistical functions (Variance, Std Dev, Z-Score, Linear Regression) are manually implemented in `core.py` to demonstrate algorithmic logic without heavy reliance on `sklearn`.

* **Anomaly Detection:** Automated flagging of tokens behaving outside standard deviation thresholds.

* **Server-Side Visualization:** Generates base64-encoded **Seaborn** & **Matplotlib** charts directly from the API.

* **Predictive Modeling:** Least Squares Linear Regression implementation for short-term price trend forecasting.

## 🛠️ Tech Stack

**Backend**

* **Core:** Python 3.x, Flask, Flask-CORS

* **Data Processing:** Pandas, NumPy, Regex

* **Visualization:** Seaborn, Matplotlib (Agg backend)

* **Data Sources:** Requests, BeautifulSoup4

**Frontend**

* **Core:** Node.js, React (located in `/frontend_app`)

* **UI:** Interactive dashboard for data consumption.

## 📂 Project Structure

...
├── api_server.py       # Flask API Entry Point & Routes
├── core.py             # Business Logic (Math, Scraper, Analysis Classes)
├── frontend_app/       # React Frontend Source Code
├── node_modules/       # Frontend Dependencies
└── README.md           # Documentation

## 🚀 Installation & Setup

**Backend Setup:**

Initialize the Python environment and install dependencies.

pip install flask flask-cors pandas numpy matplotlib seaborn beautifulsoup4 requests pymongo mongoengine
**run python file api_server.py**
**Server runs on:** http://localhost:3000

**Frontend Setup:**

Navigate to the frontend directory to start the UI.

**in command prompt:**
cd frontend_app
npm install axios react-apexcharts apexcharts
npm start

**API Endpoints:**

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/live-data` | Fetches live Binance ticker data with anomaly scores. |
| `GET` | `/api/scraped-data` | Returns cleaned data from web scraping module. |
| `GET` | `/api/analysis` | Generates statistical report (JSON + Base64 Images). |
| `GET` | `/api/history/<symbol>` | Retrieves OHLC historical data (interval support: 15m, 1h, 4h). |

## 🧠 Algorithmic Details

**The MathEngine Class:**

Located in core.py, this class replaces standard library abstractions with raw loop-based implementations for:

calculate_variance

calculate_z_score

linear_regression_predict

**Data Cleaning Strategy:**

The MessyWebScraper utilizes a strict Regex pipeline to parse human-readable currency formats (e.g., "$ 3.2 billion") into floating-point precision for analysis.

## ⚖️ Legal Disclaimer

**This software is provided for educational and research purposes only.**

* **No Financial Advice:** Nothing in this repository constitutes financial, investment, or trading advice.
* **No Warranty:** The system is provided "as is", without warranty of any kind, express or implied.
* **Risk Warning:** Cryptocurrency markets are highly volatile. The developers assume no responsibility for any financial losses or damages incurred through the use of this software.