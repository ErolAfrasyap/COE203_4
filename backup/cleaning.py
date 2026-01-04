import json
import re
from typing import Any, Dict, List, Tuple

class DataCleaner:
    @staticmethod
    def _to_float(x: Any) -> float | None:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if not s:
            return None
        s = s.replace("$", "").replace("€", "").replace("£", "").replace("%", "")
        s = s.replace(",", "")
        s = re.sub(r"\s+", "", s)
        try:
            return float(s)
        except Exception:
            return None

    @staticmethod
    def _normalize_symbol(sym: Any) -> str | None:
        if sym is None:
            return None
        s = str(sym).strip().upper()
        s = re.sub(r"[^A-Z0-9]", "", s)
        return s if s else None

    @staticmethod
    def clean_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        steps = [
            {"name": "strip_whitespace", "description": "Trim whitespace; drop empty strings"},
            {"name": "normalize_symbol", "description": "Uppercase + keep only alphanumeric for symbols"},
            {"name": "parse_money", "description": "Convert money strings to float (remove $,€,£, commas)"},
            {"name": "parse_percent", "description": "Convert percent strings to float (remove %)"},
            {"name": "drop_invalid", "description": "Drop rows missing symbol or price"},
            {"name": "deduplicate", "description": "Deduplicate by symbol (keep first)"},
        ]

        out: List[Dict[str, Any]] = []
        seen = set()

        for r in rows:
            name = r.get("name_raw")
            if isinstance(name, str):
                name = name.strip()
                if not name:
                    name = None

            symbol = DataCleaner._normalize_symbol(r.get("symbol_raw"))
            price = DataCleaner._to_float(r.get("price_raw"))
            change_24h = DataCleaner._to_float(r.get("change_24h_raw"))
            market_cap = DataCleaner._to_float(r.get("market_cap_raw"))
            source = r.get("source", "unknown")

            if symbol is None or price is None:
                continue

            if symbol in seen:
                continue
            seen.add(symbol)

            out.append(
                {
                    "name": name,
                    "symbol": symbol,
                    "price_usd": price,
                    "change_24h_pct": change_24h,
                    "market_cap_usd": market_cap,
                    "source": source,
                }
            )

        log = {
            "steps": steps,
            "input_rows": len(rows),
            "dropped": len(rows) - len(out),
            "output_rows": len(out),
        }
        return out, log

    @staticmethod
    def load_json(path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json(path: str, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
