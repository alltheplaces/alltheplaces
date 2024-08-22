from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FiatDKSpider(AgileStoreLocatorSpider):
    name = "fiat_dk"
    item_attributes = {"brand": "Fiat", "brand_wikidata": "Q27597", "extras": Categories.SHOP_CAR.value}
    allowed_domains = ["interaction.fiat.dk"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if " | " in item["name"]:
            item["name"] = item["name"].split(" | ")[1]
        yield item
