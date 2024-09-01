import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BetterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "better_gb"
    item_attributes = {
        "brand": "Better",
        "brand_wikidata": "Q109721926",
        "extras": {"leisure": "fitness_centre"},
    }
    sitemap_urls = ["https://www.better.org.uk/sitemap.xml"]
    sitemap_follow = ["leisure-centres"]
    wanted_types = ["HealthClub", "SportsActivityLocation", "ChildCare", "ExerciseGym", "StadiumOrArena"]
    sitemap_rules = [
        (r"/leisure-centre/london/[-\w]+/[-\w]+$", "parse_sd"),
        (r"/leisure-centre/[-\w]+/[-\w]+$", "parse_sd"),
    ]

    def pre_process_data(self, ld_data, **kwargs):
        rules = []
        for rule in ld_data.get("openingHours", ""):
            rules.append(re.sub(r"(\w{3})\s*-\s*(\w{3})", r"\1-\2", rule))
        ld_data["openingHours"] = rules
