from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CambridgeCityCouncilBicycleParkingUSSpider(ArcGISFeatureServerSpider):
    name = "cambridge_city_council_bicycle_parking_us"
    item_attributes = {"operator": "Cambridge City Council", "operator_wikidata": "Q133054988", "state": "MA"}
    host = "services1.arcgis.com"
    context_path = "WnzC35krSYGuYov4/ArcGIS"
    service_id = "Bike_Racks"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("Status") != "Existing":
            # Ignore proposed/rejected requests for installation of new bike
            # racks.
            return
        item["ref"] = feature["GlobalID"]
        apply_category(Categories.BICYCLE_PARKING, item)
        if capacity := feature.get("Capacity"):
            item["extras"]["capacity"] = str(capacity)
        if feature.get("Racks"):
            item["extras"]["bicycle_parking"] = "rack"
        yield item
