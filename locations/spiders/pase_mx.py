import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PaseMXSpider(scrapy.Spider):
    name = "pase_mx"
    start_urls = ["https://apps.pase.com.mx/sp-web/api/cobertura/estacionamientos"]

    def parse(self, response):
        data = response.json()
        for lot in data:
            item = Feature()
            item["ref"] = lot["id"]
            item["name"] = lot["nombre"]
            item["addr_full"] = lot["descripcion"]
            item["lat"] = lot.get("ubicacion", {}).get("coords", [{}])[0].get("y")
            item["lon"] = lot.get("ubicacion", {}).get("coords", [{}])[0].get("x")
            apply_category(Categories.PARKING, item)
            yield item
