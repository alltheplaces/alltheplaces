from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class LakelandGBSpider(StockistSpider):
    name = "lakeland_gb"
    item_attributes = {"brand": "Lakeland", "brand_wikidata": "Q16256199"}
    key = "map_83pxe5j3"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        custom_fields = {field["name"]: field["value"] for field in location["custom_fields"]}
        if store_code := custom_fields.pop("Store code", None):
            item["ref"] = store_code
        if (name := item.pop("name") or "").startswith("Lakeland "):
            item["branch"] = name.removeprefix("Lakeland ")
        item["image"] = location["image_url"]
        item["opening_hours"] = OpeningHours()
        for day, times in custom_fields.items():
            if day in DAYS_EN:
                item["opening_hours"].add_ranges_from_string(f"{day} {times}")
        if "cafe" in name.lower().replace("é", "e"):
            apply_category(Categories.CAFE, item)
        else:
            apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
