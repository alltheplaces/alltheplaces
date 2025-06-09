from locations.categories import Categories, apply_category
from locations.storefinders.yext import YextSpider


class PepeJeansSpider(YextSpider):
    name = "pepe_jeans"
    item_attributes = {"brand": "Pepe Jeans", "brand_wikidata": "Q426992"}
    api_key = "ed5d8ca6a191dbb8daeb12e8714a06c5"


def parse_item(self, item, location, **kwargs):
    item["branch"] = item.pop("name").removeprefix("Pepe Jeans ")
    apply_category(Categories.SHOP_CLOTHES, item)
    yield item
