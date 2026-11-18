import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.hamleys import HAMLEYS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class HamleysINSpider(CrawlSpider, StructuredDataSpider):
    name = "hamleys_in"
    item_attributes = HAMLEYS_SHARED_ATTRIBUTES
    start_urls = ["https://stores.hamleys.in/"]
    rules = [Rule(LinkExtractor(r"page=\d+$")), Rule(LinkExtractor("/Home"), callback="parse_sd")]
    wanted_types = ["Store"]
    time_format = "%I:%M %p"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("facebook", None)
        if branch := ld_data.get("alternateName"):
            item["branch"] = re.sub(r"\s*\bhamleys\b\s*", " ", branch, flags=re.IGNORECASE).strip() or None
        # Opening hours are only present in the page's separate LocalBusiness block
        business = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        item["opening_hours"] = LinkedDataParser.parse_opening_hours(business, time_format=self.time_format)
        apply_category(Categories.SHOP_TOYS, item)
        yield item
