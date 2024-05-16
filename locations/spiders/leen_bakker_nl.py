from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class LeenBakkerNLSpider(Spider):
    name = "leen_bakker_nl"
    item_attributes = {"brand": "Leen Bakker", "brand_wikidata": "Q3333662"}
    start_urls = ["https://www.leenbakker.nl/api/nl-NL/stores"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location["data"].update(location.pop("position"))
            item = DictParser.parse(location["data"])
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["ref"] = location["id"]
            item["website"] = response.urljoin(location["data"]["href"])

            item["opening_hours"] = OpeningHours()
            for rule in location["data"]["openingHours"]:
                if rule["displayValue"] == "Gesloten":
                    continue
                if day := sanitise_day(rule["label"], DAYS_NL):
                    item["opening_hours"].add_range(day, *rule["displayValue"].split("-"))

            yield item
