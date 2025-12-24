from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BlueBottleLiquorsZASpider(AgileStoreLocatorSpider):
    name = "blue_bottle_liquors_za"
    item_attributes = {
        "brand": "Blue Bottle Liquors",
        "brand_wikidata": "Q116861688",
    }
    allowed_domains = [
        "bluebottleliquors.co.za",
    ]
    time_format = "%I:%M%p"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
