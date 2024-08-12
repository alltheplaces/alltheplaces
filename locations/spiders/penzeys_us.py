from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PenzeysUSSpider(Spider):
    name = "penzeys_us"
    item_attributes = {"brand_wikidata": "Q7165435"}

    def start_requests(self):
        url = "https://www.penzeys.com/api/GetLocations"
        headers = {
            "Referer": "https://www.penzeys.com/locations/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        yield JsonRequest(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        for location in response.json()["Locations"]:
            item = DictParser.parse(location)
            item["state"] = location["State"]["Name"]
            item["opening_hours"] = OpeningHours()
            if "HoursOfOperation" in location:
                for hours in location["HoursOfOperation"]:
                    item["opening_hours"].add_ranges_from_string(
                        hours["daysOfWeek"] + " " + hours["timeOpen"] + "-" + hours["timeClose"]
                    )

            yield item
