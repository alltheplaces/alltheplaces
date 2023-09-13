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

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name in DAYS_FULL:
                for day_hours in location["openingHours"]:
                    if day_hours["hours"].upper() == "CLOSED":
                        break
                    if day_hours["date"] == day_name:
                        hours_string = f"{hours_string} {day_name}: " + day_hours["hours"]
                        break
                if day_name not in hours_string:
                    for day_hours in location["openingHours"]:
                        if day_hours["date"].upper() == "TODAY":
                            hours_string = f"{hours_string} {day_name}: " + day_hours["hours"]
                            break
                item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
