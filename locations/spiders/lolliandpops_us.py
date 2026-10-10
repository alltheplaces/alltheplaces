from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class LolliandpopsUSSpider(StoremapperSpider):
    name = "lolliandpops_us"
    item_attributes = {"brand": "Lolli and Pops", "brand_wikidata": "Q108410191"}
    company_id = "4652"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CONFECTIONERY, item)
        yield item
