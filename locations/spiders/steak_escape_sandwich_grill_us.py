from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SteakEscapeSandwichGrillUSSpider(StructuredDataSpider):
    name = "steak_escape_sandwich_grill_us"
    item_attributes = {"brand": "Steak Escape", "brand_wikidata": "Q7605235"}
    allowed_domains = ["steakescape.com"]
    start_urls = ["https://www.steakescape.com/locations/"]

    def parse(self, response: Response, **kwargs) -> Iterable[Request]:
        for url in response.css("a.seo-location-card::attr(href)").getall():
            yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name").removeprefix("Steak Escape ")
        yield item
