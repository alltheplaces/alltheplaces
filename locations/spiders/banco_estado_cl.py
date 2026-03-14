from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BancoEstadoCLSpider(scrapy.Spider):
    name = "banco_estado_cl"
    item_attributes = {"brand": "Banco Estado", "brand_wikidata": "Q5718188"}
    start_urls = ["https://cajavecina.gisgeoresearch.com/"]

    def parse(self, response, **kwargs):
        token = response.xpath('//*[contains(@name,"csrf-token")]/@content').get()
        for type in ["SUC", "ATM"]:
            for region in response.xpath('//*[contains(@filtro-tipo,"region")]//option/@value').getall():
                if region == "-1":
                    continue
                url = "https://cajavecina.gisgeoresearch.com/data_cajavecina"
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-CSRF-TOKEN": token,
                    "X-Requested-With": "XMLHttpRequest",
                }
                yield scrapy.FormRequest(
                    url=url,
                    headers=headers,
                    formdata={"categoria": type, "region_id": region},
                    callback=self.parse_details,
                )

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json():
            item = Feature()
            item["name"] = "Banco Estado"
            item["city"] = bank["localidad"]
            item["street"] = bank["direccion"]
            item["lat"] = bank["latitud"]
            item["lon"] = bank["longitud"]
            item["ref"] = bank["id"]
            item["housenumber"] = bank["numero"]
            if bank["tipo"] == "SUC":
                apply_category(Categories.BANK, item)
            elif bank["tipo"] == "ATM":
                apply_category(Categories.ATM, item)
            yield item
