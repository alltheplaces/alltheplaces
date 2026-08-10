from typing import Iterable

from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class NinetynineBikesAUSpider(StockistSpider):
    name = "99_bikes_au"
    item_attributes = {"brand": "99 Bikes", "brand_wikidata": "Q110288298"}
    key = "map_r3mjnyvq"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("99 Bikes ").removesuffix(" ⚡")
        item["website"] = location["custom_fields"][0]["value"]
        yield item
