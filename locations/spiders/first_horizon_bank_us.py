from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, day_range


class FirstHorizonBankUSSpider(Spider):
    name = "first_horizon_bank_us"
    item_attributes = {"brand": "First Horizon Bank", "brand_wikidata": "Q5453875"}

    async def start(self) -> AsyncIterator[FormRequest]:
        payload = {
            "Latitude": "0",
            "Longitude": "0",
            "SearchRadiusInMiles": "50000",
        }
        yield FormRequest(
            url="https://www.firsthorizon.com/api/locations/atms", formdata=payload, callback=self.parse_atms
        )
        yield FormRequest(
            url="https://www.firsthorizon.com/api/locations/branches", formdata=payload, callback=self.parse_branch
        )

    def parse_atms(self, response):
        for location in response.json()["ATMs"]:
            location["street_address"] = location.pop("Street")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = f'{location.get("Lat")}{location.get("Lng")}'
            apply_category(Categories.ATM, item)
            yield item

    def parse_branch(self, response):
        for location in response.json()["Branches"]:
            location["street_address"] = location.pop("Street")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location.get("LocationId")
            self.opening_hours(location.get("Hours"), item)
            apply_category(Categories.BANK, item)
            yield item

    def opening_hours(self, data, item):
        if not data:
            return

        oh = OpeningHours()
        for d in data:
            if time := d.get("Time"):
                if time != "Closed":
                    start_time, end_time = time.split("-")

                    if "-" in d.get("Day"):
                        days = d.get("Day").split("-")
                        oh.add_days_range(
                            day_range(DAYS_EN[days[0]], DAYS_EN[days[1]]), start_time, end_time, "%I:%M%p"
                        )
                    else:
                        oh.add_range(DAYS_EN[d.get("Day")], start_time, end_time, "%I:%M%p")

        item["opening_hours"] = oh
