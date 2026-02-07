from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.locally import LocallySpider


class AsicsUSSpider(LocallySpider):
    name = "asics_us"
    item_attributes = {"brand": "ASICS", "brand_wikidata": "Q327247"}
    company_id = 1682
    categories = ["outlet"]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        if store_name := item.pop("name", None):
            item["branch"] = store_name.removeprefix("ASICS Outlet ")
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.SHOP_SHOES, item)
        yield item
