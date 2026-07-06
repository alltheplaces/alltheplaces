from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiSudHUSpider(UberallSpider):
    name = "aldi_sud_hu"
    item_attributes = {"brand_wikidata": "Q41171672"}
    key = "rDCKKjdtbi2w0Qx3Cq1axERNtccFqZ"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["name"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
