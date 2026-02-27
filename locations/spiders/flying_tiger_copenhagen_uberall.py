from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class FlyingTigerCopenhagenUberallSpider(UberallSpider):
    name = "flying_tiger_copenhagen_uberall"
    item_attributes = {
        "brand": "Flying Tiger Copenhagen",
        "brand_wikidata": "Q2786319",
    }
    # Name is always the brand name, not a branch name
    drop_attributes = {"name"}
    key = "NDob50utCroANd8wbRBCFBYHC27U0T"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
