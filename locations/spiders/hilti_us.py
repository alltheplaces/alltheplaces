import json
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HiltiUSSpider(Spider):
    name = "hilti_us"
    item_attributes = {"brand": "Hilti", "brand_wikidata": "Q1361530"}
    start_urls = ["https://www.hilti.com/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//script[@id="hdms-website-state"]/text()').get())[
            "apollo.state"
        ].values():
            if location.get("__typename") != "HiltiCenter":
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["name"] = None
            item["branch"] = location["description"]
            item["state"] = location["address"]["region"]["__ref"].split(":", 1)[1]
            item["website"] = urljoin("https://www.hilti.com/stores/", location["slug"])

            item["opening_hours"] = OpeningHours()
            for rule in location["openingSchedule"]["days"]:
                if rule["open"] is False:
                    item["opening_hours"].set_closed(rule["day"])
                else:
                    for times in rule["workingHours"]:
                        item["opening_hours"].add_range(rule["day"], times["start"], times["end"], "%H:%M:%S")
            yield item
