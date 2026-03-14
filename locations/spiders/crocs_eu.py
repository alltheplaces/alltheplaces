from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.locally import LocallySpider


class CrocsEUSpider(LocallySpider):
    name = "crocs_eu"
    item_attributes = {"brand": "Crocs", "brand_wikidata": "Q926699"}
    company_id = 1762
    categories = ["Store", "Outlet"]
    skip_auto_cc_spider_name = True

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        if store_name := item.pop("name", None):
            item["branch"] = store_name.removeprefix("Crocs at ").removeprefix("Crocs ")
        item["street_address"] = item.pop("addr_full")
        if slug := location.get("slug"):
            item["website"] = f"https://locations.crocs.com/shop/{slug}"
        apply_category(Categories.SHOP_SHOES, item)
        yield item
