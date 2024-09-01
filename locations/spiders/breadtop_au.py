from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BreadtopAUSpider(WPStoreLocatorSpider):
    name = "breadtop_au"
    item_attributes = {"brand": "Breadtop", "brand_wikidata": "Q4959217", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = ["www.breadtop.com.au"]
    iseadgg_countries_list = ["AU"]
    search_radius = 200
    max_results = 50
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        if addr_full := item.pop("street_address", None):
            item["addr_full"] = addr_full.split(", TEL:", 1)[0]
        yield item
