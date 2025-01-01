import json

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LeonSpider(Spider):
    name = "leon"
    item_attributes = {"brand": "LEON", "brand_wikidata": "Q6524851", "extras": Categories.FAST_FOOD.value}
    start_urls = ["https://leon.co/find-leon/", "https://leon-nl.co/restaurants/"]

    def parse(self, response, **kwargs):
        for store in DictParser.get_nested_key(
            json.loads(response.xpath('//script[@type="application/json"][@id="__NEXT_DATA__"]/text()').get()),
            "restaurants",
        ):
            store["address"] = store.pop("locationDetails")
            store["address"]["city"] = store["address"].pop("townOrCity", "")
            if not store["address"].get("country"):
                store["address"]["country"] = "GB" if "leon.co" in response.url else "NL"

            item = DictParser.parse(store)

            if item["ref"] == "a-title-for-this-restaurant-and-another-one":
                continue

            item["street_address"] = store["address"].get("fullAddress")

            oh = OpeningHours()
            for rule in store.get("restaurantOpeningTimes", {}).get("openingTimes", []):
                try:
                    oh.add_range(rule["day"], rule["opensAt"], rule["closesAt"])
                except:
                    pass
            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = (
                f'https://leon.co/restaurants/{store["slug"]}/'
                if item["country"] == "GB"
                else f'https://leon-nl.co/restaurants/{store["slug"]}/'
            )

            item["extras"] = {"restaurantType": store.get("restaurantType") or store.get("type")}

            yield item
