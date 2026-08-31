from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiSudCHSpider(UberallSpider):
    name = "aldi_sud_ch"
    item_attributes = {"brand_wikidata": "Q41171672"}
    key = "lFDqKBoedhfjMheH3C3e0AcRGDuLG4"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["name"] = item["phone"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
