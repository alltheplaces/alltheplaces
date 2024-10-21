import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class NafNafESPT(Spider):
    name = "naf_naf_es_pt"
    item_attributes = {"brand_wikidata": "Q3334188"}
    start_urls = ["https://www.nafnaf.es/pages/store-locator"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//div[@id="my_markers"]').get().removesuffix("</div>").removeprefix('<div id="my_markers">')
        )["features"]:
            item = Feature()
            item["lat"] = location["properties"]["latitud"]
            item["lon"] = location["properties"]["longitud"]
            item["branch"] = location["properties"]["nombre"].removeprefix("NAFNAF ")
            item["street_address"] = location["properties"]["direccion"]
            item["city"] = location["properties"]["localidad"]
            item["postcode"] = location["properties"]["cp"]
            item["country"] = location["properties"]["pais"]
            item["phone"] = location["properties"]["tel"]
            yield item
