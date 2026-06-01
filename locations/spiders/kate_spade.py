from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class KateSpadeSpider(RioSeoSpider):
    name = "kate_spade"
    item_attributes = {"brand": "Kate Spade New York", "brand_wikidata": "Q6375797"}
    end_point = "https://maps.stores.katespade.com.prod.rioseo.com"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        feature["branch"] = feature.pop("name").removeprefix("About ").removeprefix("KSNY ")
        feature["email"] = location.get("from_email")
        apply_category(Categories.SHOP_CLOTHES, feature)
        yield feature
