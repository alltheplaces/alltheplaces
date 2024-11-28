from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_SE, OpeningHours, sanitise_day


class WillysSESpider(scrapy.Spider):
    name = "willys_se"
    item_attributes = {"brand": "Willys", "brand_wikidata": "Q10720214"}
    start_urls = ["https://www.willys.se/axfood/rest/search/store?q=*&sort=display-name-asc"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["results"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("Wh ").removeprefix("Willys ")
            item["phone"] = store["address"]["phoneNumber"]
            item["website"] = "https://www.willys.se/butik/{}".format(item["ref"])

            try:
                item["opening_hours"] = self.parse_opening_hours(store["openingHours"])
            except Exception as e:
                self.logger.error("Error parsing opening hours: {}".format(e))

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day, times = rule.split(" ")
            day = sanitise_day(day, DAYS_SE)
            if not day:
                continue
            if times in ["stängd", "00:00-00:00"]:
                oh.set_closed(day)
            else:
                oh.add_range(day, *times.split("-"))
        return oh
