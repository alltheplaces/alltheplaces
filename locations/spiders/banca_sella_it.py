from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BancaSellaITSpider(scrapy.Spider):
    name = "banca_sella_it"
    item_attributes = {"brand": "Banca Sella", "brand_wikidata": "Q3633749"}
    start_urls = ["https://www.sella.it/SSRLocatorBranch?bankAbi=03268"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["subjectId"]
            item["street_address"] = item.pop("addr_full")
            item["lat"] = location["yCoordinate"]
            item["lon"] = location["xCoordinate"]
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, bool(location["evoluedATM"]))
            oh = OpeningHours()
            for day, time in location["openingHours"].items():
                if time["composed"] == "  ":
                    oh.set_closed(day)
                else:
                    for open_close_time in time["composed"].strip().split("  "):
                        open_time, close_time = open_close_time.split("-")
                        oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh

            yield item
