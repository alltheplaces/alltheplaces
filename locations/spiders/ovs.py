import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class OvsSpider(Spider):
    name = "ovs"
    item_attributes = {"brand": "OVS", "brand_wikidata": "Q2042514", "extras": Categories.SHOP_CLOTHES.value}
    start_urls = ["https://www.ovsfashion.com/en/ie/stores/allstores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r"allStores: (\[.+\]),", response.text).group(1)):
            item = DictParser.parse(location)
            item["country"] = location["country"]["tagISO31661Alpha2"]
            item["opening_hours"] = OpeningHours()

            for day, times in zip(DAYS, location["openingHours"]):
                for time in times.split(", "):
                    if time in ["x", ""]:
                        continue
                    item["opening_hours"].add_range(day, *time.split("-"))

            yield item
