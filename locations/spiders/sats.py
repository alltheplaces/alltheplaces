import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import set_closed


# Sats (Gym chain in the nordics) is active in SE, NO, DK, FI.
# This spider is scraping the gym centers in all countries.
class SatsSpider(scrapy.Spider):
    name = "sats"
    item_attributes = {"brand": "Sats", "brand_wikidata": "Q4411496"}
    start_urls = ["https://www.sats.se/api/clubs"]

    def parse(self, response):
        for club in response.json()["clubs"]:
            item = DictParser.parse(club)
            item["city"] = item["city"].title()

            listName = club.get("listName").lower()
            if listName.startswith("hk "):
                apply_category(Categories.OFFICE_COMPANY, item)
                item["nsi_id"] = "N/A"

            if item["name"].endswith(" (closed)"):
                set_closed(item)

            yield item
