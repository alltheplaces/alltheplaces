from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MagasinVertFRSpider(JSONBlobSpider):
    name = "magasin_vert_fr"
    allowed_domains = [
        "www.monmagasinvert.fr",
    ]
    BRANDS = {
        "mv": {"brand": "Magasin Vert", "brand_wikidata": "Q16661975"},
        "pv": {"brand": "Point Vert", "brand_wikidata": "Q16661975"},
    }
    start_urls = [
        "https://www.monmagasinvert.fr/rest/mon_magasin_vert_lot1/V1/inventory/in-store-pickup/pickup-locations/?searchRequest[scopeCode]=mon_magasin_vert_lot1"
    ]
    locations_key = "items"
    needs_json_request = True

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.get("pickup_location_code")
        feature.update(feature.pop("extension_attributes", {}))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if brand_info := self.BRANDS.get(feature.get("store_type")):
            item.update(brand_info)
        yield item
