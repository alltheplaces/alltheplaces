from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ModernMarketUSSpider(AgileStoreLocatorSpider):
    name = "modern_market_us"
    item_attributes = {"brand": "Modern Market", "brand_wikidata": "Q123370165"}
    allowed_domains = ["modernmarket.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = "https://modernmarket.com/stores/{}/".format(feature["slug"])
        apply_category(Categories.RESTAURANT, item)
        yield item
