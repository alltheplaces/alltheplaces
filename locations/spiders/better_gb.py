import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BetterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "better_gb"
    item_attributes = {"brand": "Better", "brand_wikidata": "Q109721926"}
    sitemap_urls = ["https://www.better.org.uk/sitemap.xml"]
    sitemap_follow = ["leisure-centres"]
    wanted_types = ["HealthClub", "SportsActivityLocation", "ChildCare", "ExerciseGym", "StadiumOrArena"]
    sitemap_rules = [
        (r"/leisure-centre/london/[-\w]+/[-\w]+$", "parse_sd"),
        (r"/leisure-centre/[-\w]+/[-\w]+$", "parse_sd"),
    ]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        rules = []
        for rule in ld_data.get("openingHours", ""):
            rules.append(re.sub(r"(\w{3})\s*-\s*(\w{3})", r"\1-\2", rule))
        ld_data["openingHours"] = rules

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["facebook"] == "https://www.facebook.com/BetterUK/":
            item["facebook"] = None

        if item["twitter"] == "Better_UK":
            item["twitter"] = None

        apply_category(Categories.GYM, item)

        yield item
