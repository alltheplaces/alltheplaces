from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiNordESSpider(UberallSpider):
    name = "aldi_nord_es"
    item_attributes = {"brand_wikidata": "Q41171373"}
    drop_attributes = {"name"}
    key = "ALDINORDES_kRpYT2HM1bFjL9vTpn5q0JupSiXqnB"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
