import re
from typing import Any, Iterable

import chompjs
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.spiders.maverik import MaverikSpider
from locations.spiders.meijer_us import MeijerUSSpider
from locations.spiders.pilot_flying_j import FLYING_J, PILOT
from locations.spiders.schlotzskys import SchlotzskysSpider
from locations.spiders.travelcenters_of_america_us import TA
from locations.spiders.walmart_us import WalmartUSSpider
from locations.structured_data_spider import StructuredDataSpider


class CinnabonUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cinnabon_us"
    item_attributes = {"brand": "Cinnabon", "brand_wikidata": "Q1092539"}
    sitemap_urls = ["https://locations.cinnabon.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.cinnabon.com/.+?/.+?/.+", "parse_sd")]
    drop_attributes = {"image", "twitter", "facebook"}
    LOCATED_IN_MAPPINGS = [
        (["MAVERIK", "MAVERICK"], MaverikSpider.item_attributes),
        (["MEIJER"], MeijerUSSpider.item_attributes),
        (["PILOT"], PILOT),
        (["FLYING J"], FLYING_J),
        (["SCHLOTZSKY'S"], SchlotzskysSpider.item_attributes),
        (["WALMART", "WAL-MART", "WAL MART"], WalmartUSSpider.item_attributes),
        (["TA EXPRESS"], TA),
        (["BURGER KING"], BURGER_KING_SHARED_ATTRIBUTES),
    ]

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = (
            (response.xpath('//meta[@property="og:title"]/@content').get() or "")
            .split(" | ")[0]
            .removeprefix("Cinnabon ")
            .removesuffix(" Bakery")
            .strip()
        )
        if "closed" in item["branch"].lower():
            return
        item["located_in"], item["located_in_wikidata"] = extract_located_in(item["branch"], self.LOCATED_IN_MAPPINGS)
        if item["located_in"]:
            item["branch"] = " ".join(re.split(r"\s[-–]\s", item["branch"], 1)[-1].split())
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
        apply_category(Categories.FAST_FOOD, item)
        yield item
