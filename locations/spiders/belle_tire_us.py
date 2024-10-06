import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BelleTireUSSpider(Spider):
    name = "belle_tire_us"
    item_attributes = {"brand": "Belle Tire", "brand_wikidata": "Q16984061"}
    start_urls = ["https://www.belletire.com/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        )["props"]["allStores"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name").removeprefix("Belle Tire ")

            item["opening_hours"] = OpeningHours()
            for rule in location["StoreHours"]:
                if rule["Opens"] == rule["Closes"] == "Closed":
                    item["opening_hours"].set_closed(rule["Day"])
                else:
                    item["opening_hours"].add_range(rule["Day"], rule["Opens"], rule["Closes"], "%I:%M %p")

            yield item
