import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class WalkOnsUSSpider(RioSeoSpider):
    name = "walk_ons_us"
    item_attributes = {"brand": "Walk-On's Sports Bistreaux"}
    # The storefinder page is locate.walk-ons.com; its API answers on the maps. host.
    end_point = "https://maps.locate.walk-ons.com"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        # "Walk-On's Sports Bistreaux - Alexandria Restaurant", "Walk-On’s Sports Bistreaux Carencro, LA"
        feature["branch"] = re.sub(
            r"^Walk-On['’]s Sports Bistreaux\s*-?\s*|\s+Restaurant$", "", feature.pop("name", None) or ""
        ).strip()
        apply_category(Categories.RESTAURANT, feature)
        yield feature
