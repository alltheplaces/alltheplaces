import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BearesSpider(JSONBlobSpider):
    name = "beares"
    item_attributes = {"brand": "Beares", "brand_wikidata": "Q116474908"}
    start_urls = [
        "https://www.beares.co.za/storelocator",
        "https://www.beares.co.na/storelocator",
        "https://www.beares.co.bw/storelocator",
        "https://www.beares.co.ls/storelocator",
        "https://www.beares.co.sz/storelocator",
    ]

    def extract_json(self, response: Response) -> list[dict]:
        for blob in response.xpath("//*[@data-mage-init]/@data-mage-init").getall():
            if "googleMapConfig" in blob:
                return list(DictParser.get_nested_key(json.loads(blob), "stores").values())
        return []

    def pre_process_data(self, feature: dict) -> None:
        feature.pop("email", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name").removeprefix("Beares ")
        item["country"] = feature.get("country_id")

        item["opening_hours"] = OpeningHours()
        try:
            for rule in json.loads(feature.get("opening_hours") or "{}").values():
                try:
                    item["opening_hours"].add_range(rule["weekday"], rule["open_time"], rule["close_time"])
                except ValueError:
                    pass
        except AttributeError:
            pass

        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
