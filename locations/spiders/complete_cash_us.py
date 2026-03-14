from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class CompleteCashUSSpider(UberallSpider):
    name = "complete_cash_us"
    item_attributes = {"brand": "Complete Cash", "brand_wikidata": "Q132643658"}
    key = "y9nNqStSSfnX8gSmmKxyXvaKRjhh4U"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_PAWNBROKER, item)
        yield item
