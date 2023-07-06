import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class AmericaTodaySpider(Spider):
    name = "america_today"
    item_attributes = {"brand": "America Today", "brand_wikidata": "Q97011125"}
    start_urls = ["https://www.america-today.com/on/demandware.store/Sites-AmericaToday-Site/nl_NL/Stores-FindStores"]

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["house_number"] = location["houseNr"] + location["houseNrAddition"]
            location["street"] = location.pop("address1")

            item = DictParser.parse(location)

            if rules := location.get("storeHours"):
                item["opening_hours"] = OpeningHours()
                for day, start_time, end_time in re.findall(r"(\w+) (\d\d:\d\d) - (\d\d:\d\d)", rules):
                    if day := sanitise_day(day, DAYS_NL):
                        item["opening_hours"].add_range(day, start_time, end_time)

            yield item
