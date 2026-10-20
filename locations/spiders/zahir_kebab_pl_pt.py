import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ZahirKebabPLPTSpider(Spider):
    name = "zahir_kebab_pl_pt"
    item_attributes = {"brand": "Zahir Kebab", "brand_wikidata": "Q116148750"}
    start_urls = ["https://zahirkebab.pl/lokale/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@class="zkm-data"]/text()').get())
        for location in data["locations"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street", None)
            item["country"] = location["cc"]

            item["opening_hours"] = OpeningHours()
            for day, ranges in location["hours"].items():
                if not ranges:
                    item["opening_hours"].set_closed(day)
                for start, end in ranges:
                    item["opening_hours"].add_range(day, start, end)

            apply_category(Categories.FAST_FOOD, item)
            yield item
