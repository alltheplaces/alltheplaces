from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CurvesNLSpider(WPStoreLocatorSpider):
    name = "curves_nl"
    item_attributes = {"brand": "Curves", "brand_wikidata": "Q5196080"}
    start_urls = [
        "https://curves.nl/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=52.0508132&lng=5.2854055"
    ]
    days = DAYS_NL

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Curves ")
        item["website"] = response.urljoin(item["website"])
        apply_category(Categories.GYM, item)

        yield item
