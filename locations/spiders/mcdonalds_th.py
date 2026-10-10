import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsTHSpider(Spider):
    name = "mcdonalds_th"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.co.th/storeLocations"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in json.loads(re.search(r"window\.storesJson = (\[.*?\]);\s*\n", response.text).group(1)):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").title()
            item["website"] = store["detailUrl"]
            if store["is24h"]:
                item["opening_hours"] = "24/7"
            elif m := re.fullmatch(r"(\d+)\.(\d\d) - (\d+)\.(\d\d)", store["hours"]):
                oh = OpeningHours()
                oh.add_days_range(DAYS, f"{m[1]}:{m[2]}", f"{m[3]}:{m[4]}", time_format="%H:%M")
                item["opening_hours"] = oh
            apply_category(Categories.FAST_FOOD, item)
            yield item
