from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TopsDailyTHSpider(AgileStoreLocatorSpider):
    name = "tops_daily_th"
    item_attributes = {"brand": "Tops Daily", "brand_wikidata": "Q134932161"}
    allowed_domains = ["topsdaily.tops.co.th"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["addr_full"] = item.pop("street_address", None)
        item.pop("opening_hours", None)
        item.pop("website", None)
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
