from copy import deepcopy
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiCHSpider(JSONBlobSpider):
    name = "mitsubishi_ch"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://dealcore.slapwl.ch/de/mitsubishi/ch/corporate/dealer-list?filter=all"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Any:
        mitsubishi = next((brand for brand in feature.get("brands", []) if brand.get("code") == "MIT"), None)
        if not mitsubishi:
            return

        item["website"] = "https://www.mitsubishi-motors.ch/de/haendler/" + feature.get("slug", "")
        opening_hours = feature.get("dealerOpenings", {}).get("openingHours", {})

        if mitsubishi.get("sell"):
            sales_item = deepcopy(item)
            sales_item["ref"] = f"{item['ref']}-sales"
            apply_category(Categories.SHOP_CAR, sales_item)
            apply_yes_no(Extras.CAR_REPAIR, sales_item, mitsubishi.get("service", False))
            sales_item["opening_hours"] = self.parse_hours(opening_hours.get("sales"))
            yield sales_item

        if mitsubishi.get("service"):
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            service_item["opening_hours"] = self.parse_hours(opening_hours.get("service"))
            yield service_item

    @staticmethod
    def parse_hours(rules: list[dict] | None) -> OpeningHours | None:
        if not rules:
            return None
        oh = OpeningHours()
        for rule in rules:
            oh.add_range(rule["openDay"], rule["openTime"], rule["closeTime"])
        return oh
