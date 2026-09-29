from typing import Any, Iterable

import chompjs
from scrapy import Selector
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.walmart_us import WalmartUSSpider
from locations.structured_data_spider import StructuredDataSpider


class AuntieAnnesSpider(SitemapSpider, StructuredDataSpider):
    name = "auntie_annes"
    item_attributes = {"brand": "Auntie Anne's", "brand_wikidata": "Q4822010"}
    allowed_domains = ["auntieannes.com"]
    sitemap_urls = ["https://locations.auntieannes.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.auntieannes\.com/\w\w/[^/]+/[^/]+(?:/(?!\d+-dupe$)[^/]+)?$", "parse_sd")]
    drop_attributes = {"image", "twitter"}
    LOCATED_IN_MAPPINGS = [(["WALMART", "WAL-MART", "WAL MART"], WalmartUSSpider.item_attributes)]

    def extract_amenity_features(self, item: Feature | dict, selector: Selector, ld_item: dict) -> None:
        if features := ld_item.get("amenityFeature"):
            if isinstance(features, str):
                features = [features]
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in features)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in features)

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = (
            (response.xpath('//meta[@property="og:title"]/@content').get() or "")
            .split(" | ")[0]
            .replace("Auntie Anne's", "")
            .strip(" /")
            .replace(
                "Dallas Ft. Worth Int'lDallas Ft. Worth Int'l Airport (TA;G39) Airport",
                "Dallas Ft. Worth Int'l Airport (TA;G39)",
            )
            .replace(";", ":")
        )
        item["located_in"], item["located_in_wikidata"] = extract_located_in(item["branch"], self.LOCATED_IN_MAPPINGS)
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.FAST_FOOD, item)
        yield item
