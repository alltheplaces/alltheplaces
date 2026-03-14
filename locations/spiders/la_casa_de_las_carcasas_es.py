from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class LaCasaDeLasCarcasasESSpider(Spider):
    name = "la_casa_de_las_carcasas_es"
    item_attributes = {"brand": "La Casa de las Carcasas", "brand_wikidata": "Q127275290"}
    start_urls = ["https://lacasadelascarcasas.es/storefinder?ajax=1&all=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//marker"):
            item = Feature()
            item["ref"] = location.xpath("@id_store").get()
            item["lat"] = location.xpath("@lat").get()
            item["lon"] = location.xpath("@lng").get()
            item["branch"] = location.xpath("@name").get()
            item["addr_full"] = location.xpath("@addressNoHtml").get()
            item["website"] = location.xpath("@link").get()
            item["phone"] = location.xpath("@phone").get()
            item["email"] = location.xpath("@email").get()
            item["extras"]["fax"] = location.xpath("@fax").get()

            yield item
