from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class RelayFRSpider(WPStoreLocatorSpider):
    name = "relay_fr"
    item_attributes = {"brand": "Relay", "brand_wikidata": "Q3424298"}
    allowed_domains = ["www.relay.com"]
    iseadgg_countries_list = ["FR"]
    search_radius = 24
    max_results = 100

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item["name"].removeprefix("Relay ")
        item.pop("name", None)
        apply_category(Categories.SHOP_NEWSAGENT, item)
        yield item
