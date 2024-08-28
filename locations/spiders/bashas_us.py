from html import unescape
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BashasUSSpider(WPStoreLocatorSpider):
    name = "bashas_us"
    item_attributes = {
        "brand": "Bashas'",
        "brand_wikidata": "Q4866786",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.bashas.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 100
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if branch_name := item.pop("name", None):
            branch_name = unescape(branch_name)
            if branch_name.startswith("Bashas’ Diné Market"):
                item["brand"] = "Bashas’ Diné Market"
                item["branch"] = branch_name.removeprefix("Bashas’ Diné Market").removeprefix(": ")
            elif branch_name.startswith("Bashas’ Supermarket"):
                item["brand"] = "Bashas’ Supermarket"
                item["branch"] = branch_name.removeprefix("Bashas’ Supermarket").removeprefix(": ")
            if not item["branch"].strip():
                item.pop("branch", None)
        yield item
