from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_bank import LocationBankSpider


class TelkomZASpider(LocationBankSpider):
    name = "telkom_za"
    client_id = "800c7571-4e99-4efc-97e7-14983b507e31"
    item_attributes = {"brand": "Telkom", "brand_wikidata": "Q1818970"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
