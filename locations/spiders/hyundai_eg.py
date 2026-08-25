import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES

# The national corporate support hotline, repeated identically across ~47 of
# 109 locations rather than a branch-specific number.
NATIONAL_HOTLINE_DIGITS = "16661"


class HyundaiEGSpider(Spider):
    name = "hyundai_eg"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    start_urls = ["https://hyundai-egypt.net/find-us/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        seen_refs = set()
        for blob in self.extract_map_blobs(response.text):
            for place in blob.get("places", []):
                ref = place.get("id")
                if not ref or ref in seen_refs:
                    continue
                seen_refs.add(ref)

                location = place.get("location", {})
                extra_fields = location.get("extra_fields", {})
                category_name = ""
                if categories := place.get("categories"):
                    category_name = (categories[0].get("name") or "").lower()

                item = Feature()
                item["ref"] = ref
                item["name"] = place.get("title")
                item["lat"] = location.get("lat")
                item["lon"] = location.get("lng")
                item["addr_full"] = extra_fields.get("detailed-address")
                phone = extra_fields.get("phone")
                if phone and re.sub(r"\D", "", phone) != NATIONAL_HOTLINE_DIGITS:
                    item["phone"] = phone

                # The single "categories" entry present on every location
                # indicates whether it's a showroom/dealer, a service
                # centre, or a spare parts outlet.
                if "spare parts" in category_name:
                    apply_category(Categories.SHOP_CAR_PARTS, item)
                elif "after sales" in category_name or "service" in category_name:
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                else:
                    apply_category(Categories.SHOP_CAR, item)

                yield item

    def extract_map_blobs(self, html: str) -> Iterable[dict]:
        """
        Store locations are embedded in the page as the JSON argument of
        jQuery .maps({...}) calls from the "WP Google Map Gold" plugin, one
        call per map widget (showrooms/dealers, service centres, spare parts
        outlets).
        """
        for match in re.finditer(r"\.maps\(", html):
            start = match.end()
            if start >= len(html) or html[start] != "{":
                continue
            blob = self.extract_balanced_json_object(html, start)
            if blob:
                try:
                    yield json.loads(blob)
                except json.JSONDecodeError:
                    continue

    @staticmethod
    def extract_balanced_json_object(text: str, start: int) -> str | None:
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(text)):
            char = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
        return None
