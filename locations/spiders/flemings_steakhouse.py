from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class FlemingsSteakhouseSpider(CrawlSpider, StructuredDataSpider):
    name = "flemings_steakhouse"
    item_attributes = {"brand": "Fleming's", "brand_wikidata": "Q5458552"}
    start_urls = ["https://www.flemingssteakhouse.com/locations"]
    rules = [Rule(LinkExtractor(allow=r"/locations/[a-z]{2}/[^/]+/?$"), callback="parse_sd", follow=False)]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["image"] = None
        item["branch"] = item.pop("name")
        apply_category(Categories.RESTAURANT, item)

        yield item
