from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class DoughnutTimeGBSpider(StockistSpider):
    name = "doughnut_time_gb"
    item_attributes = {
        "brand_wikidata": "Q117286917",
        "brand": "Doughnut Time",
    }
    key = "u22659"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
