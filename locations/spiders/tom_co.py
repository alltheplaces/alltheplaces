from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class TomCoSpider(UberallSpider):
    name = "tom_co"
    item_attributes = {"brand": "Tom & Co", "brand_wikidata": "Q98380763"}
    key = "Aq5TVOtajZTxBQhZuFv34qsoWaXGKN"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item["name"].replace("Tom&Co ", "").replace("Tom & Co ", "")
        apply_category(Categories.SHOP_PET, item)
        yield item
