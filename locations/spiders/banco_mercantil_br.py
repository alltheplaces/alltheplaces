from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BancoMercantilBRSpider(scrapy.Spider):
    name = "banco_mercantil_br"
    item_attributes = {"brand": "Banco Mercantil do Brasil", "brand_wikidata": "Q9645252"}

    def start_requests(self):
        yield JsonRequest(
            url="https://bancomercantil.com.br/_layouts/15/MB.SHP.Internet.Portal.WebParts/ajax.aspx/getAgencias",
            data={"lat": "-23.5557714", "lng": "-46.6395571", "raio": "430", "domain": "https://bancomercantil.com.br"},
            callback=self.parse,
            method="POST",
            headers={
                "Origin": "https://bancomercantil.com.br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
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
