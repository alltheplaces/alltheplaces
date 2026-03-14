from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class WmfSpider(UberallSpider):
    name = "wmf"
    item_attributes = {"brand": "WMF", "brand_wikidata": "Q451423"}
    key = "7vItLYDhiz1DaaxSxXBEXBFzi9RILC"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("WMF ", "")
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
