import json
import glob
import os
import math
from typing import Any, Dict, List, Tuple

def _latest_clean_file() -> str | None:
    files = sorted(glob.glob(os.path.join("data", "clean", "coingecko_clean_*.json")))
    return files[-1] if files else None

def _load_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _nums(rows: List[Dict[str, Any]], key: str) -> List[float]:
    out = []
    for r in rows:
        v = r.get(key)
        if isinstance(v, (int, float)) and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            out.append(float(v))
    return out

def _mean(xs: List[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None

def _min(xs: List[float]) -> float | None:
    return min(xs) if xs else None

def _max(xs: List[float]) -> float | None:
    return max(xs) if xs else None

def _sum(xs: List[float]) -> float | None:
    return sum(xs) if xs else None

def _quantile(xs: List[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    w = pos - lo
    return s[lo] * (1 - w) + s[hi] * w

def _std(xs: List[float]) -> float | None:
    if len(xs) < 2:
        return None
    m = _mean(xs)
    if m is None:
        return None
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)

def _iqr_bounds(xs: List[float]) -> Tuple[float | None, float | None, float | None]:
    q1 = _quantile(xs, 0.25)
    q3 = _quantile(xs, 0.75)
    if q1 is None or q3 is None:
        return None, None, None
    iqr = q3 - q1
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr
    return lo, hi, iqr

def _anomalies_iqr(rows: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    xs = _nums(rows, key)
    lo, hi, iqr = _iqr_bounds(xs)
    if lo is None or hi is None:
        return []
    out = []
    for r in rows:
        v = r.get(key)
        if isinstance(v, (int, float)):
            fv = float(v)
            if fv < lo or fv > hi:
                out.append({"symbol": r.get("symbol"), "name": r.get("name"), "metric": key, "value": fv, "method": "IQR"})
    return out

def _anomalies_z(rows: List[Dict[str, Any]], key: str, z_thresh: float = 3.0) -> List[Dict[str, Any]]:
    xs = _nums(rows, key)
    m = _mean(xs)
    sd = _std(xs)
    if m is None or sd is None or sd == 0:
        return []
    out = []
    for r in rows:
        v = r.get(key)
        if isinstance(v, (int, float)):
            z = (float(v) - m) / sd
            if abs(z) >= z_thresh:
                out.append({"symbol": r.get("symbol"), "name": r.get("name"), "metric": key, "value": float(v), "z": z, "method": "Z"})
    return out

def build_report(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = ["price_usd", "change_24h_pct", "market_cap_usd"]
    summary = {}
    advanced = {}
    for k in metrics:
        xs = _nums(rows, k)
        summary[k] = {
            "count": len(xs),
            "mean": _mean(xs),
            "min": _min(xs),
            "max": _max(xs),
            "sum": _sum(xs),
        }
        q1 = _quantile(xs, 0.25)
        q2 = _quantile(xs, 0.50)
        q3 = _quantile(xs, 0.75)
        lo, hi, iqr = _iqr_bounds(xs)
        advanced[k] = {
            "q1": q1,
            "median": q2,
            "q3": q3,
            "iqr": iqr,
            "iqr_low": lo,
            "iqr_high": hi,
            "std": _std(xs),
        }

    anomalies = []
    for k in ["change_24h_pct", "price_usd", "market_cap_usd"]:
        anomalies.extend(_anomalies_iqr(rows, k))
        anomalies.extend(_anomalies_z(rows, k, 3.0))

    seen = set()
    uniq = []
    for a in anomalies:
        key = (a.get("symbol"), a.get("metric"), a.get("method"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(a)

    top_anoms = uniq[:50]

    change = _nums(rows, "change_24h_pct")
    price = _nums(rows, "price_usd")
    cap = _nums(rows, "market_cap_usd")

    narrative = []
    if change:
        narrative.append(f"24h change shows a distribution with median {(_quantile(change,0.5) or 0):.4f}% and IQR {((advanced['change_24h_pct']['iqr'] or 0)):.4f}, indicating most assets move within a narrow band while a small set exhibits extreme moves.")
    if price:
        narrative.append(f"Prices range from {(_min(price) or 0):.4f} to {(_max(price) or 0):.4f} USD with mean {(_mean(price) or 0):.4f}, reflecting a heavy-tailed market where a few large assets dominate scale.")
    if cap:
        narrative.append(f"Market cap variability is high (Q3-Q1 IQR = {((advanced['market_cap_usd']['iqr'] or 0)):.4f}), consistent with concentration in top assets.")

    if top_anoms:
        narrative.append(f"Anomaly detection flagged {len(top_anoms)} candidates using IQR and Z-score rules. These outliers can indicate unusual volatility, data glitches, or market events and should be inspected individually.")

    return {
        "row_count": len(rows),
        "summary": summary,
        "advanced": advanced,
        "anomalies": top_anoms,
        "scientific_report": "\n".join(narrative),
    }

def latest_report() -> Dict[str, Any]:
    path = _latest_clean_file()
    if not path:
        return {"error": "No clean data file found. Run scrape+clean first."}
    rows = _load_rows(path)
    rep = build_report(rows)
    rep["clean_file"] = path
    return rep

def save_latest_report(out_path: str = "data/clean/latest_analysis_report.json") -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rep = latest_report()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    return out_path

if __name__ == "__main__":
    p = save_latest_report()
    print(p)
