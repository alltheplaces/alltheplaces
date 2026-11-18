from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattlePublicLibraryUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_public_library_us"
    item_attributes = {
        "operator": "Seattle Public Library",
        "operator_wikidata": "Q7442157",
        "state": "WA",
    }
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Seattle_Public_Library"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        name = feature.get("NAME")
        if name and name.strip().upper() == "MOBILE SERVICES":
            return

        item["ref"] = feature["OBJECTID"]
        if name:
            item["name"] = name
        if address := feature.get("ADDRESS"):
            item["addr_full"] = address
        if website := feature.get("WEBSITE"):
            item["website"] = website

        apply_category(Categories.LIBRARY, item)

        yield item
