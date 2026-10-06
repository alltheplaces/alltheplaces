from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FiatDKSpider(AgileStoreLocatorSpider):
    name = "fiat_dk"
    item_attributes = {"brand": "Fiat", "brand_wikidata": "Q27597"}
    allowed_domains = ["interaction.fiat.dk"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if " | " in item["name"]:
            item["name"] = item["name"].split(" | ")[1]
        apply_category(Categories.SHOP_CAR, item)
        yield item
