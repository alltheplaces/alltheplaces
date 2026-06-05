from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class MattressFirmUSSpider(RioSeoSpider):
    name = "mattress_firm_us"
    item_attributes = {"brand": "Mattress Firm", "brand_wikidata": "Q6791878"}
    end_point = "https://maps.stores.mattressfirm.com.prod.rioseo.com"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        if feature["name"].startswith("Mattress Firm Outlet - "):
            feature["branch"] = feature.pop("name").removeprefix("Mattress Firm Outlet - ")
            feature["name"] = "Mattress Firm Outlet"
        elif feature["name"].startswith("Mattress Firm SuperCenter - "):
            feature["branch"] = feature.pop("name").removeprefix("Mattress Firm SuperCenter - ")
            feature["name"] = "Mattress Firm SuperCenter"
        else:
            feature["branch"] = feature.pop("name").removeprefix("Mattress Firm ")
            feature["name"] = "Mattress Firm"

        apply_category(Categories.SHOP_BED, feature)

        yield feature
