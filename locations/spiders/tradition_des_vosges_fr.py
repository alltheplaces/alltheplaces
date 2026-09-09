from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class TraditionDesVosgesFRSpider(UberallSpider):
    name = "tradition_des_vosges_fr"
    item_attributes = {"brand": "Tradition des Vosges", "brand_wikidata": "Q141176147"}
    key = "xP2cflp47Y6iCF9r4vY35cJ99UvjpH"
    drop_attributes = ["image", "name"]

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_HOUSEHOLD_LINEN, item)
        yield item
