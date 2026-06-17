import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed


class LeonGBSpider(Spider):
    name = "leon_gb"
    item_attributes = {"brand": "LEON", "brand_wikidata": "Q6524851"}
    start_urls = ["https://leon.co/find-leon/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in DictParser.get_nested_key(
            json.loads(response.xpath('//script[@type="application/json"][@id="__NEXT_DATA__"]/text()').get()),
            "restaurants",
        ):

            store["address"] = store.pop("locationDetails")
            store["address"]["city"] = store["address"].pop("townOrCity", "")
            if not store["address"].get("country"):
                store["address"]["country"] = "GB"

            item = DictParser.parse(store)
            item["branch"] = item.pop("name")

            if item["ref"] == "a-title-for-this-restaurant-and-another-one":
                continue

            item["addr_full"] = store["address"].get("fullAddress")

            oh = OpeningHours()
            for rule in store.get("restaurantOpeningTimes", {}).get("openingTimes", []):
                try:
                    oh.add_range(rule["day"], rule["opensAt"], rule["closesAt"])
                except:
                    pass
            item["opening_hours"] = oh

            item["website"] = (
                f'https://leon.co/restaurants/{store["slug"]}/'
                if item["country"] == "GB"
                else f'https://leon-nl.co/restaurants/{store["slug"]}/'
            )

            apply_category(Categories.FAST_FOOD, item)

            if store.get("permanentlyClosed"):
                set_closed(item)

            yield item
