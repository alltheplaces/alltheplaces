from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MoesSouthwestGrillSpider(SitemapSpider, StructuredDataSpider):
    name = "moes_southwest_grill"
    item_attributes = {
        "brand": "Moe's Southwest Grill",
        "brand_wikidata": "Q6889938",
    }
    sitemap_urls = ["https://locations.moes.com/robots.txt"]
    sitemap_rules = [
        (r"locations\.moes\.com/.*/.*/.*$", "parse_sd"),
    ]
    drop_attributes = {"image", "twitter", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if "coming soon" in response.text.lower():
            return

        item["name"] = None
        item["branch"] = (
            (response.xpath('//meta[@property="og:title"]/@content').get() or "")
            .split(" | ")[0]
            .replace("Moe's Southwest Grill", "")
            .strip()
        )

        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")

        apply_category(Categories.FAST_FOOD, item)
        yield item
