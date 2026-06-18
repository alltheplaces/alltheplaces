import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksBRSpider(Spider):
    name = "starbucks_br"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    start_urls = ["https://starbucks.harmo.me/"]  # Locator found on https://starbucks.com.br/
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in self.nuxt_state(response)["config"]["locations"]:
            item = Feature()
            item["ref"] = location["establishment_id"]
            item["addr_full"] = location["display_address"]
            item["website"] = response.urljoin(location["slug"])

            if (lat := location.get("address_latitude")) not in (None, "", "0") and (
                lon := location.get("address_longitude")
            ) not in (None, "", "0"):
                item["lat"] = lat
                item["lon"] = lon

            if location.get("openinfo_status") == "CLOSED_PERMANENTLY":
                set_closed(item)
            else:
                item["opening_hours"] = self.parse_hours(location.get("regular_hours", {}).get("periods", []))

            apply_category(Categories.COFFEE_SHOP, item)

            if item.get("lat") and item.get("lon"):
                yield item
            else:
                # The listing has no coordinates for this store, and neither does
                # its detail page. Visit the page only to capture the Google Place ID
                yield response.follow(item["website"], callback=self.parse_place_id, cb_kwargs={"item": item})

    def parse_place_id(self, response: Response, item: Feature) -> Any:
        if place_id := re.search(r"placeid=([\w-]+)", response.text):
            item["extras"]["ref:google:place_id"] = place_id.group(1)
        yield item

    def resolve_nuxt(self, idx: int, payload: list, seen: frozenset = None) -> Any:
        if seen is None:
            seen = frozenset()

        if not isinstance(idx, int) or idx < 0 or idx >= len(payload) or idx in seen:
            return None

        seen = seen | {idx}
        node = payload[idx]

        if isinstance(node, list):
            if len(node) == 2 and node[0] in ("ShallowReactive", "Reactive", "Ref"):
                return self.resolve_nuxt(node[1], payload, seen)
            return [self.resolve_nuxt(x, payload, seen) if isinstance(x, int) else x for x in node]

        if isinstance(node, dict):
            return {k: self.resolve_nuxt(v, payload, seen) if isinstance(v, int) else v for k, v in node.items()}

        return node

    def nuxt_state(self, response: Response) -> dict:
        return self.resolve_nuxt(1, json.loads(response.xpath('//script[@id="__NUXT_DATA__"]/text()').get()))["state"][
            "$sstore"
        ]

    def parse_hours(self, periods: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for period in periods:
            oh.add_range(period["openDay"].title(), period["openTime"], period["closeTime"])
        return oh
