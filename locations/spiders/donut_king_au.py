import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DonutKingAUSpider(WPStoreLocatorSpider):
    name = "donut_king_au"
    item_attributes = {"brand_wikidata": "Q5296921", "brand": "Donut King", "extras": Categories.FAST_FOOD.value}
    start_urls = ["https://www.donutking.com.au/wp/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "CLOSED" in re.split(r"\W+", item.get("name", "").upper()):
            return
        if "CLOSED" in re.split(r"\W+", item.get("addr_full", "").upper()):
            return
        if "CLOSED" in re.split(r"\W+", item.get("street_address", "").upper()):
            return
        yield item
