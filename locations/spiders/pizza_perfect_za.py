from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PizzaPerfectZASpider(WPStoreLocatorSpider):
    name = "pizza_perfect_za"
    item_attributes = {"brand_wikidata": "Q116619227", "brand": "Pizza Perfect", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "pizzaperfect.co.za",
    ]
    iseadgg_countries_list = ["ZA"]
    search_radius = 50
    max_results = 100
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix("Pizza Perfect ")
        item["phone"] = item["phone"].split("/")[0].split("|")[0]
        yield item
