from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import FIREFOX_LATEST


class BancoMercantilBRSpider(Spider):
    name = "banco_mercantil_br"
    item_attributes = {"brand": "Banco Mercantil do Brasil", "brand_wikidata": "Q9645252"}
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": FIREFOX_LATEST, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        for city in city_locations("BR", 15000):
            yield JsonRequest(
                url="https://bancomercantil.com.br/_layouts/15/MB.SHP.Internet.Portal.WebParts/ajax.aspx/getAgencias",
                data={
                    "lat": city["latitude"],
                    "lng": city["longitude"],
                    "raio": "50",
                    "domain": "https://bancomercantil.com.br",
                },
                callback=self.parse,
                method="POST",
                headers={
                    "Origin": "https://bancomercantil.com.br",
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = response.json().get("d", {}).get("agencias") or []
        for location in locations:
            item = Feature()
            item["branch"] = location["nomeAgencia"]
            item["ref"] = location["numeroAgencia"]
            item["addr_full"] = location["endereco"]
            item["phone"] = location["telefone"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            apply_category(Categories.BANK, item)
            yield item
