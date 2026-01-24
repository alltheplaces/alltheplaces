from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class O2GBSpider(SitemapSpider, StructuredDataSpider):
    name = "o2_gb"
    item_attributes = {"brand": "O2", "brand_wikidata": "Q1759255"}
    sitemap_urls = ["https://stores.o2.co.uk/robots.txt"]
    sitemap_rules = [("/o2-store-", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("O2 Shop ", "")
        yield item
