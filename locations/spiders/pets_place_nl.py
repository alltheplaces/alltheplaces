from locations.categories import apply_category, Categories
from locations.storefinders.uberall import UberallSpider
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature


class PetsPlaceNLSpider(UberallSpider):
    name = "pets_place_nl"
    item_attributes = {"brand": "Pets Place", "brand_wikidata": "Q116951772"}
    key = "FLSFmn17JhB8QiJQD7stjGbDIi9Q56"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_PET, item)
        yield item
