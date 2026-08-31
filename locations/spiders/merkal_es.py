import json
import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

TIME_RANGE_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*h?\s*a\s*(\d{1,2})(?::(\d{2}))?\s*h?", re.IGNORECASE)


class MerkalESSpider(Spider):
    name = "merkal_es"
    item_attributes = {"brand": "Merkal", "brand_wikidata": "Q126894589"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.merkal.com/api/2026-01/graphql.json",
            headers={"X-Shopify-Storefront-Access-Token": "48e6681567bb31aeaa7dbd82c04f1ce9"},
            data={
                "query": (
                    '{ v1: metaobject(handle: {handle: "bss_sl_metaobject_data", '
                    'type: "$app:bss_sl_data_v1"}) { fields { key value } } }'
                )
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for field in (response.json().get("data") or {}).get("v1", {}).get("fields", []):
            if not field.get("key", "").startswith("locations_"):
                continue
            for location in json.loads(field["value"]).get("data", []):
                if not location.get("storeName", "").startswith("Merkal"):
                    continue
                item = DictParser.parse(location)
                item["branch"] = item.pop("name").removeprefix("Merkal").strip()
                item["ref"] = str(location["id"])
                item["street_address"] = merge_address_lines(
                    [location.get("address"), location.get("additional_address")]
                )
                item.pop("addr_full", None)
                item["email"] = None  # all stores share the brand-level address infoclientes@merkal.com
                item["lat"], item["lon"] = location["lat"], location["lng"]

                item["opening_hours"] = OpeningHours()
                try:
                    schedule = json.loads(location.get("schedule") or "[]")
                except ValueError:
                    schedule = []
                for entry in schedule:
                    day = sanitise_day(entry.get("date") or "")
                    value = entry.get("value")
                    if not day or not isinstance(value, str):
                        continue
                    if value.strip().lower() == "cerrado":
                        item["opening_hours"].set_closed(day)
                        continue
                    for open_h, open_m, close_h, close_m in TIME_RANGE_RE.findall(value):
                        item["opening_hours"].add_range(
                            day, f"{open_h}:{open_m or '00'}", f"{close_h}:{close_m or '00'}"
                        )

                apply_category(Categories.SHOP_SHOES, item)
                yield item
