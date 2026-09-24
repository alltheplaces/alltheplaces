from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JambaJuiceSpider(SitemapSpider, StructuredDataSpider):
    name = "jamba_juice"
    item_attributes = {"brand": "Jamba", "brand_wikidata": "Q3088784"}
    allowed_domains = ["jamba.com"]
    sitemap_urls = ["https://locations.jamba.com/sitemap.xml"]
    sitemap_rules = [(r"/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    drop_attributes = {"image", "twitter", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.FAST_FOOD, item)
        yield item
