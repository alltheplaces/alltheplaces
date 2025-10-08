from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class PepesPiriPiriGBSpider(UberallSpider):
    name = "pepes_piri_piri_gb"
    item_attributes = {"brand": "Pepe's", "brand_wikidata": "Q120645662"}
    key = "AvaxP06WrnMGLVlO7F1k5uryHxCd0R"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
