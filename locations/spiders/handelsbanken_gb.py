import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class HandelsbankenGBSpider(scrapy.Spider):
    name = "handelsbanken_gb"
    item_attributes = {"brand": "Handelsbanken", "brand_wikidata": "Q1421630"}
    start_urls = ["https://www.handelsbanken.co.uk/rsoia/parg/bu/branches/v3/country/GB/en"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            if location["branchUrl"]:
                item["website"] = "https://" + location["branchUrl"]
            else:
                continue

            oh = OpeningHours()
            for day in location["openingHours"]:
                oh.add_range(DAYS[int(day.get("weekday"))], day.get("openTime"), day.get("closeTime"))
            item["opening_hours"] = oh

            apply_category(Categories.BANK, item)

            yield item
