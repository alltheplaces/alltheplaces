from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DoroITSpider(WPStoreLocatorSpider):
    name = "doro_it"
    item_attributes = {"brand": "Doro Supermercati", "brand_wikidata": "Q136464598"}
    allowed_domains = ["www.dorosupermercati.it"]
    iseadgg_countries_list = ["IT"]
    search_radius = 100
    max_results = 100

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "Daily" in item["name"]:
            item["name"] = "Doro Daily"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            item["name"] = "Doro Supermercati"
            apply_category(Categories.SHOP_SUPERMARKET, item)

        if state := item.get("state"):
            item["state"] = state.strip("()")

        yield item
