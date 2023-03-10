from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class AdairsSpider(Spider):
    name = "adairs"
    item_attributes = {"brand": "Adairs", "brand_wikidata": "Q109626904"}
    allowed_domains = ["www.adairs.com.au", "www.adairs.co.nz"]
    start_urls = [
        "https://www.adairs.com.au/api/store/search-store",
        "https://www.adairs.co.nz/api/store/search-store",
    ]

    def start_requests(self):
        data = {
            "pageId": 665,
            "pageNumber": 1,
            "pageSize": 1000,
        }
        for url in self.start_urls:
            if "adairs.com.au" in url:
                data["marketId"] = "AUS"
            elif "adairs.co.nz" in url:
                data["marketId"] = "NEZ"
            yield JsonRequest(url=url, method="POST", data=data, callback=self.parse)

    def parse(self, response):
        if not response.json()["success"]:
            return
        for location in response.json()["payload"]["items"]:
            item = DictParser.parse(location)
            if " - CLOSED" in item["name"].upper():
                continue
            if "Adairs Kids" in item["name"]:
                item["brand"] = "Adairs Kids"
            if "adairs.com.au" in response.url:
                item["website"] = "https://www.adairs.com.au" + location["link"]["url"]
            elif "adairs.co.nz" in response.url:
                item["website"] = "https://www.adairs.co.nz" + location["link"]["url"]

            oh = OpeningHours()
            for day_name in DAYS_FULL:
                open_time = None
                close_time = None
                for day_hours in location["openingHours"]:
                    if day_hours["hours"].upper() == "CLOSED":
                        break
                    if day_hours["date"] == day_name:
                        open_time = day_hours["hours"].split(" - ")[0]
                        close_time = day_hours["hours"].split(" - ")[1]
                        break
                if not open_time and not close_time:
                    for day_hours in location["openingHours"]:
                        if day_hours["date"].upper() == "TODAY":
                            open_time = day_hours["hours"].split(" - ")[0]
                            close_time = day_hours["hours"].split(" - ")[1]
                            break
                if ":" not in open_time:
                    open_time = open_time.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
                if ":" not in close_time:
                    close_time = close_time.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
                oh.add_range(day_name, open_time, close_time, "%I:%M %p")
            item["opening_hours"] = oh.as_opening_hours()

            yield item
