from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class YvesRocherITSpider(UberallSpider):
    name = "yves_rocher_it"
    item_attributes = {"brand": "Yves Rocher", "brand_wikidata": "Q1477321"}
    key = "HLGRPp968JZaR0D235dXJa5fMRPHuA"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("image", None)

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
