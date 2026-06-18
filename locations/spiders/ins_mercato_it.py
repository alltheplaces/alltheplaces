from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class InsMercatoITSpider(Spider):
    name = "ins_mercato_it"
    item_attributes = {"brand": "In's Mercato", "brand_wikidata": "Q105615834"}
    start_urls = ["https://www.insmercato.it/punti-vendita"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//input[@data-id]"):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            # TODO: location.xpath('@data-slug').get()
            item["branch"] = location.xpath("@data-title").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["addr_full"] = location.xpath("@data-address").get()
            item["phone"] = location.xpath("@data-phone").get().replace(" / ", "")

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
