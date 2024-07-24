from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, DAYS_CZ, DAYS_EN, DAYS_SK, OpeningHours, sanitise_day


class BillaSpider(Spider):
    name = "billa"
    allowed_domains = ["www.billa.at", "www.billa.bg", "www.billa.sk", "www.billa.cz"]
    start_urls = [
        "https://www.billa.at/api/stores",
        "https://www.billa.bg/api/stores",
        "https://www.billa.sk/api/stores",
        "https://www.billa.cz/api/stores",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        days = DAYS_EN
        wikidata = "Q537781"
        if "billa.bg" in response.url:
            days = DAYS_BG
        elif "billa.sk" in response.url:
            days = DAYS_SK
        elif "billa.cz" in response.url:
            days = DAYS_CZ
            wikidata = "Q42969493"

        for location in response.json():
            if not location.get("open") and not location.get("openingTimes"):
                continue
            if "billa.cz" in response.url and "phone" in location:
                location["phone"] = "+420" + location["phone"][1:]
            item = DictParser.parse(location)
            item.pop("name")
            item["brand_wikidata"] = wikidata
            item["lon"] = location["position"]["lng"]
            item["lat"] = location["position"]["lat"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingTimes"]:
                if len(day_hours.get("times", [])) != 2:
                    continue
                if day := sanitise_day(day_hours["dayOfWeek"].strip(":"), days):
                    item["opening_hours"].add_range(day, day_hours["times"][0], day_hours["times"][1])
            if "parking" in location and "spotCount" in location["parking"]:
                item["extras"]["capacity:motorcar"] = location["parking"]["spotCount"]
            yield item
