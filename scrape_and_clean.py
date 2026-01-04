import os
import sys
import subprocess
from datetime import datetime
from cleaning import DataCleaner
from analysis_report import run_analysis


def run_scrape_and_clean():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/clean", exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_out = f"data/raw/coingecko_raw_{ts}.json"
    clean_out = f"data/clean/coingecko_clean_{ts}.json"
    log_out = f"data/clean/coingecko_cleaning_log_{ts}.json"

    cmd = [
        sys.executable,
        "-m",
        "scrapy",
        "runspider",
        "scraper/spiders/coingecko_top_spider.py",
        "-O",
        raw_out,
    ]
    subprocess.run(cmd, check=True)

    rows = DataCleaner.load_json(raw_out)
    cleaned, log = DataCleaner.clean_rows(rows)

    DataCleaner.save_json(clean_out, cleaned)
    DataCleaner.save_json(log_out, log)

    analysis_json, analysis_md = save_analysis_files(cleaned, base_dir="data")

    return raw_out, clean_out, log_out, analysis_json, analysis_md
