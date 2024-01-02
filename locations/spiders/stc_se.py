import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


# Sats (Gym chain in the nordics) is active in SE, NO, DK, FI.
# This spider is scraping the gym centers in all countries.
class StcSESpider(scrapy.Spider):
    name = "stc_se"
    item_attributes = {"brand": "STC", "brand_wikidata": "Q124061743"}
    start_urls = ["https://www.stc.se/assets/clubs.json"]

    def parse(self, response):
        for club in response.json():
            item = DictParser.parse(club)
            item["branch"] = item["name"]
            item["branch"] = item.pop("name")
            item["city"] = item["city"].title()

            yield item
