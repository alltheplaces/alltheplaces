from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ActionSpider(Spider):
    name = "action"
    item_attributes = {"brand": "Action", "brand_wikidata": "Q2634111"}
    start_urls = ["https://www.action.com/api/stores/all/"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["items"]:
            location_id = location["id"]
            yield JsonRequest(url=f"https://www.action.com/api/stores/{location_id}/", callback=self.parse_location)

    def parse_location(self, response):
        location = response.json()["data"]
        if location["permanentlyClosedDate"]:
            return
        item = DictParser.parse(location)
        item["ref"] = location["branchNumber"]
        item["name"] = location["store"]
        item["housenumber"] = "".join(filter(None, [location["houseNumber"], location["houseNumberAddition"]]))
        item["street"] = location["street"]
        item["website"] = "https://www.action.com" + location["url"]
        item["opening_hours"] = OpeningHours()
        for day_hours in location["openingHours"]:
            if day_hours["thisWeek"]["closed"]:
                continue
            item["opening_hours"].add_range(
                day_hours["dayName"], day_hours["thisWeek"]["opening"], day_hours["thisWeek"]["closing"]
            )
        yield item
