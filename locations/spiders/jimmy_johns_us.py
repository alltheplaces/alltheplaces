from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JimmyJohnsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "jimmy_johns_us"
    item_attributes = {"brand": "Jimmy John's", "brand_wikidata": "Q1689380"}
    allowed_domains = ["locations.jimmyjohns.com"]
    sitemap_urls = ["https://locations.jimmyjohns.com/sitemap.xml"]
    sitemap_rules = [(r"sandwiches", "parse_sd")]
    drop_attributes = {"image", "twitter", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.FAST_FOOD, item)
        yield item
