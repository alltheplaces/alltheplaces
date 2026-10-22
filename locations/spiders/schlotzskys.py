from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SchlotzskysSpider(SitemapSpider, StructuredDataSpider):
    name = "schlotzskys"
    item_attributes = {"brand": "Schlotzsky's", "brand_wikidata": "Q2244796"}
    sitemap_urls = ["https://locations.schlotzskys.com/robots.txt"]
    sitemap_rules = [(r"/\d[^/]*$", "parse")]
    wanted_types = ["FastFoodRestaurant"]
    drop_attributes = {"twitter", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["name"] = None
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.FAST_FOOD, item)
        yield item
