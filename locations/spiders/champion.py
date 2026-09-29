import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class ChampionSpider(StockistSpider):
    name = "champion"
    item_attributes = {"brand": "Champion", "brand_wikidata": "Q2948688"}
    key = "map_w3rk47yq"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(r"^champion\s+(?:store\s+)?", "", item.pop("name"), flags=re.IGNORECASE)
        item["opening_hours"] = OpeningHours()
        for custom_field in location["custom_fields"]:
            if custom_field["name"] in DAYS_FULL:
                day = DAYS_EN[custom_field["name"]]
                if custom_field["value"] == "x":
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_ranges_from_string(f"{day} {custom_field['value']}")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
