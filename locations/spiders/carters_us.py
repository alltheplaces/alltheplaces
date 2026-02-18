from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CartersUSSpider(SitemapSpider, StructuredDataSpider):
    name = "carters_us"
    item_attributes = {"brand": "Carter's", "brand_wikidata": "Q5047083"}
    allowed_domains = ["www.carters.com"]
    sitemap_urls = ["https://www.carters.com/sitemap_index.xml"]
    sitemap_rules = [
        (r"https://www.carters.com/l/.*/.*/.*", "parse_sd"),
    ]
    time_format = "%I:%M%p"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        oh = OpeningHours()
        for day_time in ld_data["openingHours"]:
            oh.add_ranges_from_string(day_time)
        item["opening_hours"] = oh
        yield item
