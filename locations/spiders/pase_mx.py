from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PaseMXSpider(Spider):
    name = "pase_mx"
    start_urls = ["https://apps.pase.com.mx/sp-web/api/cobertura/estacionamientos"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lot in response.xpath("//item"):
            item = Feature()
            item["ref"] = lot.xpath("id/text()").get()
            item["branch"] = lot.xpath("nombre/text()").get()
            item["addr_full"] = lot.xpath("descripcion/text()").get()
            item["lat"] = lot.xpath("ubicacion/coords/y/text()").get()
            item["lon"] = lot.xpath("ubicacion/coords/x/text()").get()

            if operator := lot.xpath(".//nombreoperador/text()").get():
                item["operator"] = operator.strip()

            apply_category(Categories.PARKING, item)
            yield item
