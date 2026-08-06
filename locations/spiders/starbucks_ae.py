from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StarbucksAESpider(SitemapSpider, StructuredDataSpider):
    name = "starbucks_ae"
    item_attributes = {"brand": "ستاربكس", "brand_wikidata": "Q37158"}
    sitemap_urls = ["https://locations.starbucks.ae/robots.txt"]
    sitemap_rules = [(r"^https://locations\.starbucks\.ae/(?!ar/)[^/]+/[^/]+$", "parse")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = response.xpath("//h1/text()").get("").removeprefix("Starbucks ")
        item["website"] = response.url
        yield item
