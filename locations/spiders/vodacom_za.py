from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_bank import LocationBankSpider

VODACOM = {"brand": "Vodacom", "brand_wikidata": "Q1856518"}


class VodacomZASpider(LocationBankSpider):
    name = "vodacom_za"
    client_id = "19ced8ad-ae12-440c-abb5-423a1d49a002"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        name = item.get("name") or ""
        if name.startswith("Vodacom 4U "):
            item.update(VODACOM)
            item["branch"] = item.pop("name").removeprefix("Vodacom 4U ")
            item["name"] = "Vodacom 4U"
        elif name.startswith("Vodacom "):
            item.update(VODACOM)
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
