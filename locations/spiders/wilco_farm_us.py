import json
import re
from typing import Any, Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WilcoFarmUSSpider(JSONBlobSpider):
    name = "wilco_farm_us"
    item_attributes = {"brand": "Wilco", "brand_wikidata": "Q8000290"}
    allowed_domains = ["farmstore.com"]
    start_urls = ["https://www.farmstore.com/locations/"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        payload = json.loads(response.xpath('//script[@id="__NUXT_DATA__"]/text()').get())
        store_keys = {"storeNumber", "name", "address", "phone", "metadata", "storeHours"}
        return [
            self.resolve(payload, index)
            for index, node in enumerate(payload)
            if isinstance(node, dict) and store_keys <= node.keys()
        ]

    def resolve(self, payload: list, index: Any, seen: tuple[int, ...] = ()) -> Any:
        if not isinstance(index, int) or not (0 <= index < len(payload)) or index in seen:
            return None if isinstance(index, int) else index
        node = payload[index]
        seen = seen + (index,)
        if isinstance(node, dict):
            return {key: self.resolve(payload, child, seen) for key, child in node.items()}
        if isinstance(node, list):
            return [self.resolve(payload, child, seen) for child in node]
        return node

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("storeNumber")

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removesuffix(" Farm Store")
        metadata = location.get("metadata")
        item["lat"] = metadata.get("latitude")
        item["lon"] = metadata.get("longitude")

        item["opening_hours"] = self.parse_hours(location.get("storeHours") or [])
        apply_category(Categories.SHOP_AGRARIAN, item)

        yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours:
        opening_hours = OpeningHours()
        for line in lines:
            for start_day, end_day, start_time, start_ap, end_time, end_ap in re.findall(
                r"(\w+)(?:\s*through\s*(\w+))?:\s*(\d{1,2}(?::\d{2})?)\s*([ap])\.m\.\s*to\s*(\d{1,2}(?::\d{2})?)\s*([ap])\.m\.",
                line,
                re.IGNORECASE,
            ):
                end_day = end_day or start_day
                if ":" not in start_time:
                    start_time += ":00"
                if ":" not in end_time:
                    end_time += ":00"
                opening_hours.add_days_range(
                    day_range(start_day, end_day),
                    f"{start_time} {start_ap.upper()}M",
                    f"{end_time} {end_ap.upper()}M",
                    time_format="%I:%M %p",
                )
        return opening_hours
