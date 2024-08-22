from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class RefuelDoubleQuickUSSpider(AgileStoreLocatorSpider):
    name = "refuel_double_quick_us"
    item_attributes = {"extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["www.refuelmarket.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["title"].startswith("Refuel "):
            item["brand"] = "Refuel"
            item["brand_wikidata"] = "Q124987140"
        elif feature["title"].startswith("Double Quick "):
            item["brand"] = "Double Quick"
            item["brand_wikidata"] = "Q124987186"
        item["ref"] = feature["title"].split(" ")[-1]
        yield item
