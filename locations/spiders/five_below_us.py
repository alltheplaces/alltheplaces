from typing import Any, Iterable

import chompjs
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FiveBelowUSSpider(SitemapSpider, StructuredDataSpider):
    name = "five_below_us"
    item_attributes = {"brand": "Five Below", "brand_wikidata": "Q5455836"}
    drop_attributes = {"image", "name", "facebook"}
    allowed_domains = ["locations.fivebelow.com"]
    sitemap_urls = ["https://locations.fivebelow.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
