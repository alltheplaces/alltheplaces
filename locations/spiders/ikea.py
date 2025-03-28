from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

ALT_TYPES = {
    "bistro": ({"name": "IKEA Bistro"}, Categories.FAST_FOOD),
    "cafe": ({}, Categories.CAFE),
    "clickncollect": None,
    "restaurant": ({"name": "IKEA Restaurant"}, Categories.FAST_FOOD),
    "smaland": ({}, Categories.LEISURE_INDOOR_PLAY),
    "swedishFoodMarket": ({}, Categories.SHOP_CONVENIENCE),
}


class IkeaSpider(scrapy.Spider):
    name = "ikea"
    item_attributes = {"brand": "IKEA", "brand_wikidata": "Q54078"}
    allowed_domains = ["ikea.com", "ikea.cn"]
    start_urls = [
        "https://www.ikea.com/ae/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/bh/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/eg/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/jo/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/kw/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ma/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/qa/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/sa/ar/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/cz/cs/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/dk/da/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/at/de/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/de/de/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/au/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ca/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/gb/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ie/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/in/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ph/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/sg/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/us/en/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/cl/es/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/es/es/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/mx/es/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/fi/fi/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/be/fr/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ch/fr/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/fr/fr/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/il/he/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/hr/hr/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/hu/hu/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/it/it/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/jp/ja/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/kr/ko/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/my/ms/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/nl/nl/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/no/no/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/pl/pl/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/pt/pt/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ro/ro/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/sk/sk/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/si/sl/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/rs/sr/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/se/sv/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/th/th/meta-data/informera/stores-detailed.json",
        "https://www.ikea.com/ua/uk/meta-data/informera/stores-detailed.json",
        "https://www.ikea.cn/cn/zh/meta-data/informera/stores-detailed.json",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if store["buClassification"]["code"] == "FFP":  # FULFILMENT POINT
                continue

            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["name"] = None
            item["branch"] = store["displayName"].replace("IKEA", "").strip()
            item["country"] = response.url.split("/")[3].upper()
            if item["country"] == "US":
                item["state"] = store["address"].get("stateProvinceCode")[2:]

            item["website"] = (
                store["storePageUrl"]
                if "storePageUrl" in store
                else response.url.replace("/meta-data/informera/stores-detailed.json", "/stores/")
            )

            for alt, hours in store.get("hours", {}).items():
                if not hours:
                    continue
                if cat := ALT_TYPES.get(alt):
                    alt_item = item.deepcopy()
                    alt_item.update(cat[0])
                    alt_item["ref"] = "{}-{}".format(item["ref"], alt)
                    alt_item["opening_hours"] = self.parse_opening_hours(hours)

                    apply_category(cat[1], alt_item)
                    yield alt_item

            try:
                item["opening_hours"] = self.parse_opening_hours(store.get("hours", {}).get("normal") or [])
            except:
                self.logger.error("Error parsing opening hours")

            if item["country"] in ("DE", "PT"):
                item["name"] = "IKEA"

            item["extras"]["store_type"] = store["buClassification"]["code"]
            item["extras"]["start_date"] = store["openCloseDates"]["openingDate"].replace("T00:00:00Z", "")
            item["extras"]["ref:google:place_id"] = store.get("placeId")

            apply_category(Categories.SHOP_FURNITURE, item)
            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            oh.add_range(rule["day"], rule["open"], rule["close"])
        return oh
