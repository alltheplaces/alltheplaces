from typing import Iterable

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class BananaRepublicHomeUSSpider(StockistSpider):
    name = "banana_republic_home_us"
    item_attributes = {
        "brand": "Banana Republic Home",
        "brand_wikidata": "Q129793169",
        "extras": Categories.SHOP_FURNITURE.value,
    }
    key = "u17439"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        if "COMING SOON" in item["name"].upper():
            return

        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix("BR HOME ")

        if hours_string := feature.get("description", None):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

        yield item
