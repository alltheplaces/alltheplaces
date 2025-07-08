from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import sanitise_day
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class CircleKNOSpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k_no"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.no/stations"]
    rules = [Rule(LinkExtractor(allow=r"/station/[-\w]+/?$"), callback="parse")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        if any(sanitise_day(rule) for rule in ld_data.get("openingHours", [])):  # day without hours
            ld_data.pop("openingHours")

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not ld_data.get("openingHours"):
            ld_data["openingHours"] = []
            for rule in response.xpath('//*[@itemprop="openingHours"]'):
                day = rule.xpath("./@content").get()
                hours = rule.xpath("./text()").get("").replace("Døgnåpent", "00:00-23:59")  # open 24 hours
                ld_data["openingHours"].append(f"{day} {hours}")
        item["opening_hours"] = LinkedDataParser.parse_opening_hours(ld_data)

        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item
