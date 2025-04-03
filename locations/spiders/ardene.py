from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class ArdeneSpider(UberallSpider):
    name = "ardene"
    item_attributes = {"brand": "Ardene", "brand_wikidata": "Q2860764"}
    key = "APLOifTJjDLpXnd0K1bTlQmbKKM3mt"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
