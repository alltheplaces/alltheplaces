from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import FIREFOX_LATEST


class BancoMercantilBRSpider(scrapy.Spider):
    name = "banco_mercantil_br"
    item_attributes = {"brand": "Banco Mercantil do Brasil", "brand_wikidata": "Q9645252"}
    custom_settings = {"USER_AGENT": FIREFOX_LATEST, "ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://bancomercantil.com.br/_layouts/15/MB.SHP.Internet.Portal.WebParts/ajax.aspx/getAgencias",
            data={"lat": "-23.5557714", "lng": "-46.6395571", "raio": "430", "domain": "https://bancomercantil.com.br"},
            callback=self.parse,
            method="POST",
            headers={
                "Origin": "https://bancomercantil.com.br",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["d"]["agencias"]:
            item = Feature()
            item["branch"] = location["nomeAgencia"]
            item["ref"] = location["numeroAgencia"]
            item["addr_full"] = location["endereco"]
            item["phone"] = location["telefone"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            apply_category(Categories.BANK, item)
            yield item
