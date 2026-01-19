from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GrandOpticalSpider(SitemapSpider, StructuredDataSpider):
    name = "grand_optical"
    item_attributes = {"brand": "GrandOptical", "brand_wikidata": "Q3113677"}
    sitemap_urls = ["https://www.grandoptical.com/sitemap.xml"]
    sitemap_rules = [(r"/opticien/[^/]+/\d+", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url
        yield item
