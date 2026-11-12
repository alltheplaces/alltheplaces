from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class StaplesCASpider(RioSeoSpider):
    name = "staples_ca"
    item_attributes = {"brand": "Staples", "brand_wikidata": "Q17149420"}
    end_point = "https://maps.stores.staples.ca"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        if feature["ref"].startswith("CA-W-"):
            return
        apply_category(Categories.SHOP_STATIONERY, feature)
        yield feature
