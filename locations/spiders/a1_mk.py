from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class A1MKSpider(Spider):
    name = "a1_mk"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q24589907"}
    start_urls = ["https://www.a1.mk/o/StoreFinder-portlet/rest/api/shops/"]

    def parse(self, response):
        for location in response.json():
            if not location.get("isOpen"):
                continue
            item = DictParser.parse(location)
            item["branch"] = location["nameMK"]

            if location["shopType"]["shopGroup"]["metadata"] != "centers":
                # Ignore partner stores.
                continue
            if location.get("code"):
                item["ref"] = location["code"]
            item["name"] = location.get("nameMK")
            item["extras"]["name:mk"] = location.get("nameMK")
            item["extras"]["name:en"] = location.get("nameEN")
            item["extras"]["name:sq"] = location.get("nameAL")
            item["street_address"] = location.get("addressMK")
            item["city"] = location["city"].get("nameMK")
            item["opening_hours"] = OpeningHours()
            if location.get("workingWeekWorkPeriod") and location["workingWeekWorkPeriod"].strip() != "-":
                item["opening_hours"].add_days_range(
                    ["Mo", "Tu", "We", "Th", "Fr"], *location["workingWeekWorkPeriod"].split(" - "), "%H:%M"
                )
            if location.get("saturdayWorkingPeriod") and location["saturdayWorkingPeriod"].strip() != "-":
                item["opening_hours"].add_range("Sa", *location["saturdayWorkingPeriod"].split(" - "), "%H:%M")
            if location.get("sundayWorkingPeriod") and location["sundayWorkingPeriod"].strip() != "-":
                item["opening_hours"].add_range("Su", *location["sundayWorkingPeriod"].split(" - "), "%H:%M")
            yield item
