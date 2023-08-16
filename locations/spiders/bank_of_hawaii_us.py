import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BankOfHawaiiUSSpider(scrapy.Spider):
    name = "bank_of_hawaii_us"
    item_attributes = {"brand": "Bank of Hawaii", "brand_wikidata": "Q4856124"}
    allowed_domains = ["boh.com"]
    start_urls = ["https://www.boh.com/bohapi/get-locations?lat=21.33&lng=-157.845934&radius=250"]

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["lat"] = location["geocode"]["latitude"]
            item["lon"] = location["geocode"]["longitude"]
            oh = OpeningHours()
            for day_name, day in location["operationalHours"]["hours"].items():
                if day["isClosed"]:
                    continue
                for hours_range in day["hours"]:
                    oh.add_range(day_name.title(), hours_range["openTime"], hours_range["closeTime"], "%H:%M:%S")
            # Branch without an ATM
            if "Branch" in location["type"] and "ATM" not in location["type"]:
                apply_category(Categories.BANK, item)
                item["opening_hours"] = oh.as_opening_hours()
            # Branch with an ATM
            elif "Branch" in location["type"] and "ATM" in location["type"]:
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, True)
                item["opening_hours"] = oh.as_opening_hours()
            # ATM only
            elif "Branch" not in location["type"] and "ATM" in location["type"]:
                apply_category(Categories.ATM, item)
            yield item
