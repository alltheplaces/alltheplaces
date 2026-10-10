import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class RainsSpider(StockistSpider):
    name = "rains"
    item_attributes = {"brand": "Rains", "brand_wikidata": "Q119440481"}
    key = "map_63vme57q"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Rains Store ")
        # Some locations state hours in French notation, such as "11h-14h / 15h-19h".
        hours_string = re.sub(
            r"(\d{1,2})h(\d{2})?",
            lambda match: "{}:{}".format(match.group(1), match.group(2) or "00"),
            location["description"],
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(re.sub(r"\s+", " ", hours_string))
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
