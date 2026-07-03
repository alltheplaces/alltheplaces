from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category, Categories
from locations.google_url import extract_google_position
from locations.items import Feature


class MeliMeloSpider(Spider):
    name = "meli_melo"
    item_attributes = {"brand": "Meli Melo", "brand_wikidata": "Q134389410"}
    start_urls = ["https://www.melimeloparis.ro/magazine"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//table/tbody/tr"):
            item = Feature()
            item["branch"] = location.xpath("./td[1]/span/text()").get().removeprefix("Meli Melo ")
            item["addr_full"] = location.xpath("./td[2]/text()").get()
            extract_google_position(item, location)
            apply_category(Categories.SHOP_FASHION_ACCESSORIES, item)
            yield item
