from typing import Iterable

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class StrandbagsAUSpider(StockistSpider):
    name = "strandbags_au"
    item_attributes = {"brand": "Strandbags", "brand_wikidata": "Q111946652", "extras": Categories.SHOP_BAG.value}
    key = "u8518"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        hours_text = location.get("description").replace("\\n", " ")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
