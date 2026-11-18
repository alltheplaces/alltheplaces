from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class OutbackSteakhouseSpider(SitemapSpider, StructuredDataSpider):
    name = "outback_steakhouse"
    item_attributes = {"brand": "Outback Steakhouse", "brand_wikidata": "Q1064893"}
    sitemap_urls = ["https://locations.outback.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.outback.com/[^/]+/[^/]+/[^/]+(?:/\d+)?$", "parse_sd")]

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        if "CLOSED" in item["name"]:
            return
        item["branch"] = item.pop("name").removeprefix("Outback Steakhouse").strip(" -")
        yield item
