🚀 Crypto Analytics System – Real-Time Binance Tracking & Analysis Application

This project is a desktop application that tracks cryptocurrency data from Binance in real time, analyzes market trends, visualizes token price history, and stores all data in MongoDB Atlas for persistent storage.

The system is built using Tkinter, Matplotlib, Requests, MongoEngine, Pydantic, and Scrapy.
The project can also be compiled into a Windows executable (.exe) for systems without Python installed.

1️⃣ Project Purpose

The goal of this project is to:

Track the top N Binance USDT pairs in real time

Provide users with live price, percentage change, and volume data

Generate market analysis reports (top gainers and losers)

Show detailed views and price charts for selected tokens

Persist token snapshots and historical price records in MongoDB

Perform additional data scraping via Scrapy

This application demonstrates the fundamental components of a crypto market analytics tool.

2️⃣ Use Cases
🔹 2.1 — Real-Time Market Tracking

When the user clicks START STREAM:

The system retrieves live market data from Binance

Displays:

Price

24h percentage change

Session percentage change (since stream start)

24h volume

The table continuously updates during the session.

🔹 2.2 — Market Analysis (Gainers / Losers)

When the ANALYZE button is pressed, the system generates a report containing:

Top 5 gainers

Top 5 losers

Total number of analyzed assets

Timestamp of the analysis

This summary is displayed inside the analysis panel.

🔹 2.3 — Token Detail & Price Chart

When a token is selected (or double-clicked):

A separate window opens showing:

Token ID, name, price, volume, 24h change, category

A price chart of the last ~30 days

A summary of the last 5 days

This helps visualize short-term market trends.

🔹 2.4 — MongoDB Atlas Data Storage

The application saves all fetched data to MongoDB:

TokenDocument — current token snapshot

HistoricalDocument — historical price records

When the program is restarted, previously saved token data is loaded automatically and displayed in the table.

🔹 2.5 — Scrapy-Based Data Collection

The RUN SCRAPY button:

Dynamically generates a Scrapy spider (binance_spider.py)

Executes it using:

python -m scrapy runspider binance_spider.py -o binance_data.json


Saves the output into binance_data.json inside the project directory

This JSON file can be used for offline analysis or dataset preparation.

3️⃣ Project Structure

The project uses a flat directory layout as required:

.
├── core.py         # API requests, MongoDB models, data classes, analytics
├── main.py         # Application entry point (launches Tkinter GUI)
├── ui.py           # TK interface, tables, charts, Scrapy integration
├── main.exe        # Compiled Windows executable
├── test.py         # Test file (optional)
└── README.md       # Documentation

4️⃣ How to Run the Application
🔹 4.1 — Running from Source (Python)
Requirements:

Python 3.10+

Internet connection

MongoDB Atlas account (or local MongoDB)

Install dependencies:
pip install pymongo mongoengine pydantic requests scrapy dnspython matplotlib


If using a virtual environment:

python -m venv venv
venv\Scripts\activate

Start the application:
python main.py --limit 50

🔹 4.2 — Running via Executable (Windows)

Launch the program by double-clicking:

main.exe


Python installation is not required.

To generate your own executable:

pyinstaller --onefile --noconsole main.py


The executable will be located in:

/dist/main.exe

5️⃣ Known Issues & Limitations
Issue	Description
Binance API rate limits	Excessive request frequency may cause temporary throttling.
Network / DB failures	Internet or MongoDB outages produce read/write errors.
Scrapy dependency	Scrapy must be installed for JSON export to work.
MongoDB URI inside code	For demonstration only; production requires environment variables.
Missing historical data	When API history is unavailable, a flat synthetic dataset is shown.

Despite these limitations, the system operates reliably for demonstration and coursework purposes.