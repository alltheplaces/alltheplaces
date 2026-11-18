from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MattressDepotUsaUSSpider(WPStoreLocatorSpider):
    name = "mattress_depot_usa_us"
    item_attributes = {"brand": "Mattress Depot USA", "brand_wikidata": "Q108413386"}
    start_urls = [
        "https://www.mattressdepotusa.com/wp-admin/admin-ajax.php?action=store_search&lat=47.60621&lng=-122.33207&max_results=100&search_radius=500"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removesuffix(" Store")
        apply_category(Categories.SHOP_BED, item)
        yield item
