from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SixtyVinesUSSpider(StructuredDataSpider):
    name = "sixty_vines_us"
    item_attributes = {"brand": "Sixty Vines"}
    start_urls = ["https://www.sixtyvines.com/locations"]
    wanted_types = ["Restaurant"]

    def parse(self, response: Response) -> Iterable[Request]:
        yield from response.follow_all(xpath='//a[starts-with(@href, "/locations/")]/@href', callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name").removeprefix("Sixty Vines - ")
        apply_category(Categories.RESTAURANT, item)
        yield item
