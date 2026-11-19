import json
import re
from typing import Any, Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PanarottisSpider(JSONBlobSpider):
    name = "panarottis"
    item_attributes = {"brand": "Panarottis", "brand_wikidata": "Q130220087"}
    start_urls = ["https://www.panarottis.com/za/restaurants/all"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        payload = json.loads(response.xpath('//script[@id="__NUXT_DATA__"]/text()').get())
        return [
            self.resolve(payload, index)
            for index, node in enumerate(payload)
            if isinstance(node, dict) and {"api_id", "latitude", "longitude"} <= node.keys()
        ]

    def resolve(self, payload: list, index: int) -> Any:
        node = payload[index]
        if isinstance(node, dict):
            return {key: self.resolve(payload, child) for key, child in node.items()}
        if isinstance(node, list):
            return [self.resolve(payload, child) for child in node]
        return node

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("api_id")

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        if location.get("status") != "Open" or location.get("temporarily_closed") or not item.get("lat"):
            return

        item["branch"] = re.sub(r"^Panarottis\s+", "", item.pop("name"))
        item["website"] = item["website"].split("?")[0]

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            hours = location.get(day.lower()) or {}
            if hours.get("open") and hours.get("close"):
                item["opening_hours"].add_range(day, hours["open"], hours["close"], "%H:%M:%S")

        attributes = {a["name"]: a.get("value") for a in location.get("attributes") or []}
        apply_category(Categories.RESTAURANT, item)
        apply_yes_no(Extras.DELIVERY, item, bool(attributes.get("Delivery")))
        apply_yes_no(Extras.TAKEAWAY, item, bool(attributes.get("Takeaway")))
        apply_yes_no(Extras.WHEELCHAIR, item, bool(location.get("is_wheelchair_accessible")))
        apply_yes_no(Extras.WIFI, item, bool(location.get("has_wireless_internet")))

        yield item
