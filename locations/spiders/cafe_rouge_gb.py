from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class CafeRougeGBSpider(FrankieAndBennysGBSpider):
    name = "cafe_rouge_gb"
    item_attributes = {"brand": "Café Rouge", "brand_wikidata": "Q5017261"}
    start_urls = ["https://www.caferouge.com/restaurants"]

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = response.xpath('//*[@class="restaurant-title"]/text()').get("").removeprefix("Center Parcs ")
        yield item
