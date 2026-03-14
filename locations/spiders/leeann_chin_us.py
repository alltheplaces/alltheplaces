from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LeeannChinUSSpider(CrawlSpider, StructuredDataSpider):
    name = "leeann_chin_us"
    item_attributes = {
        "brand": "Leeann Chin",
        "brand_wikidata": "Q6515716",
    }
    start_urls = ["https://www.leeannchin.com/locations"]
    rules = [Rule(LinkExtractor(allow=r"/restaurant/[-\w]+/[-\w]+/?$"), callback="parse_sd")]
    json_parser = "chompjs"
    drop_attributes = {"facebook", "twitter"}

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data.pop("openingHoursSpecification", None)  # Current day is missing from ld_data

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = item["name"].removesuffix(" Fresh Asian Flavors")
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//*[@class="opening-hours"]//li'):
            item["opening_hours"].add_ranges_from_string(rule.xpath("./text()").get())
        yield item
