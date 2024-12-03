from datetime import datetime

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class NettoSallingSpider(Spider):
    name = "netto_salling"
    item_attributes = {"brand": "Netto", "brand_wikidata": "Q552652"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for country in ["DE", "DK", "PL"]:
            yield JsonRequest(
                url="https://api.sallinggroup.com/v2/stores?country={}&geo?&radius=100&per_page=1000".format(country),
                headers={"Authorization": "Bearer b1832498-0e22-436c-bd18-9ffa325dd846"},
            )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["lon"], item["lat"] = location["coordinates"]
            item["street_address"] = item.pop("street")

            try:
                item["opening_hours"] = self.parse_opening_hours(location["hours"])
            except:
                self.logger.error("Error parsing opening hours")

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule["type"] != "store":
                continue
            day = DAYS[datetime.strptime(rule["date"], "%Y-%m-%d").weekday()]
            if rule["closed"] is True:
                oh.set_closed(day)
            else:
                oh.add_range(
                    day,
                    datetime.fromisoformat(rule["open"]).timetuple(),
                    datetime.fromisoformat(rule["close"].replace("T24:00:00", "T23:59:00")).timetuple(),
                )
        return oh
