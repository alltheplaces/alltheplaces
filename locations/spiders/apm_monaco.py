from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class ApmMonacoSpider(StoremapperSpider):
    name = "apm_monaco"
    item_attributes = {
        "brand": "APM Monaco",
        "brand_wikidata": "Q85738954",
    }
    company_id = "12892"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_JEWELRY, item)
        item["name"] = "APM Monaco"

        fields = [
            location.get("custom_field_1") or "",
            location.get("custom_field_2") or "",
            location.get("custom_field_3") or "",
        ]

        if any(fields):
            oh = OpeningHours()
            oh.add_ranges_from_string(" ".join(fields))
            item["opening_hours"] = oh
        else:
            item["opening_hours"] = None

        yield item
