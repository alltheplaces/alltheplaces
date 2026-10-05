import json
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LeonGBSpider(Spider):
    name = "leon_gb"
    item_attributes = {"brand": "LEON", "brand_wikidata": "Q6524851"}
    start_urls = ["https://leon.co/find-leon/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stream = ""
        for script in response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall():
            chunk = chompjs.parse_js_object(script)
            if len(chunk) > 1 and isinstance(chunk[1], str):
                stream += chunk[1]
        for line in stream.splitlines():
            data = line.partition(":")[2]
            if data[:1] in ("[", "{"):
                for payload in DictParser.iter_matching_keys(json.loads(data), "payload"):
                    for store in payload:
                        if isinstance(store, dict) and "locationDetails" in store:
                            yield from self.parse_store(store)

    def parse_store(self, store: dict) -> Any:
        if store.get("permanentlyClosed") or store.get("comingSoon") or store.get("closed"):
            return

        store["address"] = store.pop("locationDetails")
        store["address"]["city"] = store["address"].pop("townOrCity", "")
        if not store["address"].get("country"):
            store["address"]["country"] = "GB"

        item = DictParser.parse(store)
        item["branch"] = item.pop("name")

        if item["ref"] == "a-title-for-this-restaurant-and-another-one":
            return

        item["addr_full"] = store["address"].get("fullAddress")
        item["phone"] = (store.get("contactDetails") or {}).get("phoneNumber")

        oh = OpeningHours()
        for rule in (store.get("restaurantOpeningTimes") or {}).get("openingTimes") or []:
            try:
                oh.add_range(rule["day"], rule["opensAt"], rule["closesAt"])
            except:
                pass
        item["opening_hours"] = oh

        item["website"] = f'https://leon.co/restaurants/{store["slug"]}/'

        apply_category(Categories.FAST_FOOD, item)

        yield item
