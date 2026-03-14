from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BendCityCouncilBicycleParkingUSSpider(ArcGISFeatureServerSpider):
    name = "bend_city_council_bicycle_parking_us"
    item_attributes = {"operator": "Bend City Council", "operator_wikidata": "Q134540047", "state": "OR"}
    host = "services5.arcgis.com"
    context_path = "JisFYcK2mIVg9ueP/ArcGIS"
    service_id = "BikeRacks"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["globalid"]
        apply_category(Categories.BICYCLE_PARKING, item)
        item["extras"]["bicycle_parking"] = "rack"
        if capacity := feature.get("capacity"):
            item["extras"]["capacity"] = capacity
        if covered := feature.get("covered"):
            if covered == "No":
                item["extras"]["covered"] = "no"
            elif covered == "Yes":
                item["extras"]["covered"] = "yes"
        yield item
