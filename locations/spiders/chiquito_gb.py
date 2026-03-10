from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class ChiquitoGBSpider(FrankieAndBennysGBSpider):
    name = "chiquito_gb"
    item_attributes = {"brand": "Chiquito", "brand_wikidata": "Q5101775"}
    start_urls = ["https://www.chiquito.co.uk/restaurants"]

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = response.xpath('//*[@class="restaurant-title"]/text()').get("")
        yield item
