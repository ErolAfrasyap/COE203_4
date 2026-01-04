# Crypto Analytics System v4 — Scrape + Clean + Analysis + Seaborn + React Dashboard

## Features & Grading Coverage

### Visualization
- Matplotlib (baseline): Used via Tkinter canvas embedding (FigureCanvasTkAgg).
- Seaborn (+5): Histogram + KDE and Boxplot for 24h change distribution.
- Web-based React visualization (+15): React + Plotly dashboard renders histogram, box plot, scatter, and anomaly list.

### Dataset
- Downloaded messy data (+5): Raw output saved into `data/raw/` in unnormalized string formats.
- Scraped messy web data (+10): Data is collected using a Scrapy spider from a web page (HTML) and stored as raw fields:
  - `name_raw`, `symbol_raw`, `price_raw`, `change_24h_raw`, `market_cap_raw`
  - Output: `data/raw/coingecko_raw_YYYYMMDD_HHMMSS.json`
- Clean dataset (baseline): Cleaned data saved into `data/clean/` as normalized numeric fields:
  - `price_usd`, `change_24h_pct`, `market_cap_usd`

### Analysis
- Simple aggregations (baseline): mean, min, max, sum per metric.
- Advanced statistics (+5): quartiles (Q1/median/Q3), IQR bounds, standard deviation; box plot visualization.
- Data science (+15): anomaly detection with IQR rule and Z-score rule; scientific-style summary report.

## Cleaning Pipeline (Step-by-step)
The cleaning stage converts messy scraped strings into a reliable dataset:

1) **strip_whitespace**
- Trim leading/trailing whitespace and drop empty strings for `name_raw`.

2) **normalize_symbol**
- Convert symbols to uppercase and keep only alphanumeric characters.
- Example: " btc " → "BTC", "eth-2" → "ETH2"

3) **parse_money**
- Convert price/market cap strings to floats:
- Remove currency symbols ($,€,£), commas, and spaces.
- Example: "$90,381.00" → 90381.0

4) **parse_percent**
- Convert percent strings to floats:
- Remove `%` and convert to numeric.
- Example: "0.63%" → 0.63

5) **drop_invalid**
- Drop rows where `symbol` or `price` is missing after parsing.

6) **deduplicate**
- Deduplicate by `symbol` to keep one row per asset.

Cleaning logs are saved as:
- `data/clean/coingecko_cleaning_log_YYYYMMDD_HHMMSS.json`

## Anomaly Detection Method
Two methods are applied to metrics:
- `change_24h_pct`, `price_usd`, `market_cap_usd`

**IQR Method**
- Compute Q1, Q3, IQR = Q3 - Q1
- Outliers if value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR

**Z-score Method**
- Compute mean and standard deviation
- Flag if |z| >= 3.0

The top anomalies are included in:
- `data/clean/latest_analysis_report.json`
and displayed in both UI and React dashboard.

## How to Run

### 1) Run Tkinter UI
```bash
python main.py
