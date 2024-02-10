from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class StorepointSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "storepoint.co"}
    key = ""
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(url=f"https://api.storepoint.co/v1/{self.key}/locations")

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            return

        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)
            item["lat"] = location["loc_lat"]
            item["lon"] = location["loc_long"]
            item["addr_full"] = item.pop("street_address")
            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day in DAYS_FULL:
                if hours_for_day := location.get(day.lower()):
                    if "24 HOURS" in hours_for_day.upper():
                        hours_for_day = "00:00 - 24:00"
                    hours_string = f"{hours_string} {day}: {hours_for_day}"
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield from self.parse_item(item, location)

    def parse_item(self, item, location: {}, **kwargs):
        yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool:
        if len(response.xpath('//div[@id="storepoint-container"]/@data-map-id')) > 0:
            return True
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict:
        return {
            "key": response.xpath('//div[@id="storepoint-container"]/@data-map-id').get(),
        }
