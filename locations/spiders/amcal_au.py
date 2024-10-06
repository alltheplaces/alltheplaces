from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class AmcalAUSpider(Spider):
    name = "amcal_au"
    item_attributes = {"brand": "Amcal", "brand_wikidata": "Q63367373"}

    def start_requests(self):
        data = {
            "businessid": "4",
            "latitude": "0",
            "longitude": "0",
            "session_id": "0000000000000000000000000000000000000000",
        }
        headers = {"Origin": "https://amcal.com.au"}
        yield JsonRequest(
            url="https://app.medmate.com.au/connect/api/get_locations", data=data, headers=headers, method="POST"
        )

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = location["locationname"]
            item["website"] = (
                "https://amcal.com.au/store/"
                + str(location["locationid"])
                + "/"
                + location["state"]
                + "/"
                + location["slug"]
                + "/"
            )
            data = {
                "businessid": "4",
                "include_services": True,
                "locationid": str(location["locationid"]),
                "session_id": "0000000000000000000000000000000000000000",
            }
            headers = {"Origin": "https://amcal.com.au"}
            yield JsonRequest(
                url="https://app.medmate.com.au/connect/api/get_pharmacy",
                data=data,
                headers=headers,
                method="POST",
                meta={"item": item},
                callback=self.add_opening_hours,
            )

    def add_opening_hours(self, response):
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in response.json()["trading_hours"].items():
            if day_name not in DAYS_FULL:
                continue
            # Open and closes at 12AM is closed in this context; so only
            # add hours when they differ.
            if day_hours["open"] != day_hours["closed"]:
                item["opening_hours"].add_range(day_name, day_hours["open"], day_hours["closed"], "%I:%M %p")
        yield item
