import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.iceland_foods import IcelandFoodsSpider


class TheFoodWarehouseGBSpider(IcelandFoodsSpider):
    name = "the_food_warehouse_gb"
    item_attributes = {"brand": "The Food Warehouse", "brand_wikidata": "Q87263899"}

    def wanted(self, branch: str) -> bool:
        return self.is_food_warehouse(branch)

    def post_process_item(self, item: Feature) -> Iterable[Feature]:
        item["branch"] = re.sub(r"\s*(FWH|FOOD WAR\w*|E?HOUSE?)\b.*$", "", item["branch"], flags=re.IGNORECASE).strip(
            " -("
        )
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
