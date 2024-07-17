from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class EverGreenTWSpider(Spider):
    name = "ever_green_tw"
    item_attributes = {"brand": "Ever Green", "brand_wikidata": "Q126369781"}
    start_urls = ["https://www.ai-drugstore.com/store-locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//*[@data-post-id]"):
            item = Feature()
            item["ref"] = location.xpath("./@data-post-id").get()
            item["website"] = location.xpath(".//a/@href").get()
            item["name"], item["addr_full"], item["phone"] = location.xpath(
                './/*[contains(@class,"elementor-heading-title")]/text()'
            ).getall()[:3]
            apply_category(Categories.PHARMACY, item)
            yield item
