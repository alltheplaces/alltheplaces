from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BILLAATSpider(Spider):
    name = "billa_at"
    item_attributes = {"brand": "BILLA", "brand_wikidata": "Q537781"}
    allowed_domains = ["billa.at"]
    start_urls = ["https://www.billa.at/api/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if not location["open"]:
                continue
            item = DictParser.parse(location)
            item["lon"] = location["coordinate"]["x"]
            item["lat"] = location["coordinate"]["y"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingTimes"]:
                item["opening_hours"].add_range(day_hours["dayOfWeek"], day_hours["times"][0], day_hours["times"][1])
            if "parking" in location and "spotCount" in location["parking"]:
                item["extras"]["capacity:motorcar"] = location["parking"]["spotCount"]
            yield item
