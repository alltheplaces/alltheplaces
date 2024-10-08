from typing import Iterable

from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class PandoraSpider(RioSeoSpider):
    name = "pandora"
    item_attributes = {"brand": "Pandora", "brand_wikidata": "Q2241604"}
    end_point = "https://maps.pandora.net"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        feature["phone"] = location.get("location_phone") or location.get("local_phone")
        feature["postcode"] = location.get("location_post_code") or location.get("post_code")
        feature["website"] = "https://stores.pandora.net/"
        if location.get("Store Type_CS") == "Authorized Retailers":
            feature["extras"]["secondary"] = "yes"
        yield feature
