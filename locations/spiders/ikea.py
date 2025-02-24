from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class IkeaSpider(scrapy.Spider):
    name = "ikea"
    item_attributes = {"brand": "IKEA", "brand_wikidata": "Q54078"}
    allowed_domains = ["ikea.com"]
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
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["opening_hours"] = OpeningHours()
            if hours := store.get("hours", {}).get("normal"):
                for rule in hours:
                    if day := sanitise_day(rule.get("day")):
                        item["opening_hours"].add_range(
                            day,
                            rule["open"],
                            rule["close"],
                        )
            split_url = response.url.split("/")
            country_path = f"{split_url[3]}/{split_url[4]}"

            item["branch"] = store["displayName"]
            item["country"] = split_url[3].upper()
            item["website"] = (
                store["storePageUrl"] if "storePageUrl" in store else f"https://www.ikea.com/{country_path}/stores/"
            )
            item["extras"]["store_type"] = store["buClassification"]["code"]

            if item["country"] == "US":
                item["state"] = store["address"].get("stateProvinceCode")[2:]

            apply_category(Categories.SHOP_FURNITURE, item)
            yield item
