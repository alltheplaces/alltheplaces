from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class LakelandGBSpider(StockistSpider):
    name = "lakeland_gb"
    item_attributes = {"brand": "Lakeland", "brand_wikidata": "Q16256199"}
    key = "map_83pxe5j3"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Lakeland ")
        item["image"] = location["image_url"]
        item["opening_hours"] = OpeningHours()
        for field in location["custom_fields"]:
            open_time, close_time = field["value"].split(" - ")
            item["opening_hours"].add_range(field["name"], open_time, close_time)
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
