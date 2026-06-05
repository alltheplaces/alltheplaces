from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class MattressFirmUSSpider(RioSeoSpider):
    name = "mattress_firm_us"
    end_point = "https://maps.stores.mattressfirm.com.prod.rioseo.com"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        # Maintain original brand separation
        if "Clearance" in location.get("location_name", ""):
            feature["brand"] = "Mattress Firm Clearance"
            feature["brand_wikidata"] = "Q6791878"
        else:
            feature["brand"] = "Mattress Firm"
            feature["brand_wikidata"] = "Q6791878"

        feature["branch"] = (
            feature.pop("name", "")
            .removeprefix("Mattress Firm ")
            .replace("Mesa Clearance Center at ", "")
            .replace("Outlet", "")
            .strip(" -")
        )
        apply_category(Categories.SHOP_BED, feature)

        yield feature
