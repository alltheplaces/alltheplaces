from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AnglingDirectGBSpider(Spider):
    name = "angling_direct_gb"
    item_attributes = {"brand": "Angling Direct", "brand_wikidata": "Q119276672"}
    allowed_domains = ["www.anglingdirect.co.uk"]
    start_urls = ["https://www.anglingdirect.co.uk/storelocator/ajax/search"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", headers={"X-Requested-With": "XMLHttpRequest"})

    def parse(self, response):
        for location in response.json():
            if location["coming_soon"] != "0":
                continue
            if location["store_status"] is not None:
                return
            item = DictParser.parse(location)
            item["ref"] = location["location_id"]
            item["website"] = "https://www.anglingdirect.co.uk/storelocator/" + item["name"].replace(
                "Angling Direct ", ""
            ).lower().replace(" ", "-")
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location["opening_hours"].items():
                if "CLOSED" in day_hours.upper():
                    continue
                item["opening_hours"].add_range(
                    day_name.title(), day_hours.split(" - ", 1)[0], day_hours.split(" - ", 1)[1]
                )
            yield item
