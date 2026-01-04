import glob
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Crypto Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def latest_clean_file():
    files = sorted(glob.glob("data/clean/coingecko_clean_*.json"))
    return files[-1] if files else None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/latest")
def latest():
    path = latest_clean_file()
    if not path:
        return {"path": None, "count": 0, "rows": []}
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {"path": path, "count": len(rows), "rows": rows}
