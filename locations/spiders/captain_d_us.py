from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CaptainDUSSpider(SitemapSpider, StructuredDataSpider):
    name = "captain_d_us"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    sitemap_urls = ["https://locations.captainds.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.FAST_FOOD, item)
        yield item
