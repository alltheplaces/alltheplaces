import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AliorBankPLSpider(Spider):
    name = "alior_bank_pl"
    item_attributes = {"brand": "Alior Bank", "brand_wikidata": "Q9148395"}
    start_urls = ["https://www.aliorbank.pl/en/branches.html"]

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath("//script[@id='branch']/text()").get())
        for city, branches in data.items():
            for branch in branches:
                item = Feature()
                item["postcode"] = branch["pc"]
                item["city"] = city
                item["street_address"] = branch["s"]
                item["name"] = branch["n"]
                item["lat"] = branch["lt"]
                item["lon"] = branch["lg"]
                item["ref"] = branch["o"]
                self.parse_opening_hours(item, branch["h"])
                apply_category(Categories.BANK, item)
                yield item

    # based on _renderOpenHours in JavaScript
    def parse_opening_hours(self, item, openings):
        item["opening_hours"] = OpeningHours()
        if openings[-1]["d"] == "7":
            item["opening_hours"].add_ranges_from_string(f"Mo-Fr {openings[-1]['h']}")
            for opening in openings[:-1]:
                item["opening_hours"].add_ranges_from_string(f"{DAYS[int(opening['d'])]} {opening['h']}")
        else:
            for opening in openings:
                item["opening_hours"].add_ranges_from_string(f"{DAYS[int(opening['d'])]} {opening['h']}")
