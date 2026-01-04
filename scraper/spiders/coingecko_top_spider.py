import json
import scrapy

class CoingeckoTopSpider(scrapy.Spider):
    name = "coingecko_top"
    allowed_domains = ["api.coingecko.com"]

    def start_requests(self):
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
            "&sparkline=false&price_change_percentage=24h"
        )
        yield scrapy.Request(url, callback=self.parse, headers={"Accept": "application/json"})

    def parse(self, response):
        data = json.loads(response.text)
        for r in data:
            yield {
                "name_raw": r.get("name"),
                "symbol_raw": r.get("symbol"),
                "price_raw": r.get("current_price"),
                "change_24h_raw": r.get("price_change_percentage_24h"),
                "market_cap_raw": r.get("market_cap"),
                "source": "coingecko_api",
            }
