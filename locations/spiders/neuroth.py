from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NeurothSpider(SitemapSpider, StructuredDataSpider):
    name = "neuroth"
    item_attributes = {"brand": "Neuroth", "brand_wikidata": "Q15836645"}
    sitemap_urls = ["https://www.neuroth.com/robots.txt"]
    sitemap_rules = [(r".+/filialen|lokacije|poslovnice|/[^/]+/$", "parse_sd")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("name")
        yield item
