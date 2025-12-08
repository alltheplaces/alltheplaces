from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class GoodlifePharmacyKESpider(AgileStoreLocatorSpider):
    name = "goodlife_pharmacy_ke"
    item_attributes = {"brand": "Goodlife Pharmacy", "brand_wikidata": "Q120783615"}
    allowed_domains = ["www.goodlife.co.ke"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.PHARMACY, item)
        yield item
