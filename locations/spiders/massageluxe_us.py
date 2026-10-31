from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class MassageluxeUSSpider(AgileStoreLocatorSpider):
    name = "massageluxe_us"
    item_attributes = {"brand": "MassageLuXe"}
    allowed_domains = ["massageluxe.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["ref"] = feature["id"]

        apply_category(Categories.SHOP_MASSAGE, item)

        yield item
