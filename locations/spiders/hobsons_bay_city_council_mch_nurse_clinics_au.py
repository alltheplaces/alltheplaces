from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HobsonsBayCityCouncilMchNurseClinicsAUSpider(ArcGISFeatureServerSpider):
    name = "hobsons_bay_city_council_mch_nurse_clinics_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    host = "services3.arcgis.com"
    context_path = "gToGKwidNkZbWBGJ/ArcGIS"
    service_id = "MCH_Pt"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["No"])
        item.pop("addr_full", None)
        item["street_address"] = feature["Address"]
        item["city"] = feature["Suburb"]
        apply_category(Categories.NURSE_CLINIC, item)
        yield item
