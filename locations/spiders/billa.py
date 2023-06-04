from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, DAYS_CZ, DAYS_SK, OpeningHours


class BILLASpider(Spider):
    name = "billa"
    item_attributes = {"brand": "BILLA", "brand_wikidata": "Q537781"}
    allowed_domains = ["www.billa.at", "www.billa.bg", "www.billa.sk", "www.billa.cz"]
    start_urls = ["https://www.billa.at/api/stores", "https://www.billa.bg/api/stores", "https://www.billa.sk/api/stores", "https://www.billa.cz/api/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if not location.get("open") and not location.get("openingTimes"):
                continue
            item = DictParser.parse(location)
            item["lon"] = location["coordinate"]["x"]
            item["lat"] = location["coordinate"]["y"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingTimes"]:
                if len(day_hours.get("times", [])) != 2:
                    continue
                if "billa.bg" in response.url:
                    day_name = DAYS_BG[day_hours["dayOfWeek"][:2].title()]
                elif "billa.sk" in response.url:
                    day_name = DAYS_SK[day_hours["dayOfWeek"][:2].title()]
                elif "billa.cz" in response.url:
                    day_name = DAYS_CZ[day_hours["dayOfWeek"][:2].title()]
                else:
                    day_name = day_hours["dayOfWeek"]
                item["opening_hours"].add_range(day_name, day_hours["times"][0], day_hours["times"][1])
            if "parking" in location and "spotCount" in location["parking"]:
                item["extras"]["capacity:motorcar"] = location["parking"]["spotCount"]
            yield item
