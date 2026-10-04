from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider

# Needler's runs the Agile Store Locator WordPress plugin, which returns every
# store in one admin-ajax.php response.
#
# The plugin's open_hours field holds "0" for every day rather than times,
# which the store finder reads as closed, so hours are dropped.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class NeedlersFreshMarketUSSpider(AgileStoreLocatorSpider):
    name = "needlers_fresh_market_us"
    item_attributes = {"brand": "Needler's Fresh Market"}
    allowed_domains = ["needlersfreshmarket.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)
        # Each day of open_hours is "0" rather than a time, which the store
        # finder reads as closed; the stores are not closed, so hours are
        # dropped.
        item["opening_hours"] = None

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
