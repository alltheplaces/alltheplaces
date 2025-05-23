from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BendCityCouncilCrossingsUSSpider(ArcGISFeatureServerSpider):
    name = "bend_city_council_crossings_us"
    item_attributes = {"operator": "Bend City Council", "operator_wikidata": "Q134540047", "state": "OR"}
    host = "services5.arcgis.com"
    context_path = "JisFYcK2mIVg9ueP/ArcGIS"
    service_id = "Crosswalks"
    layer_id = "7"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FacilityID"]

        # Convert LineString of two coordinates to a midpoint coordinate.
        # May change back to LineString in the future if ATP starts extracting
        # more complex geometries than just Point.
        item["lat"] = (item["geometry"]["coordinates"][0][1] + item["geometry"]["coordinates"][1][1]) / 2
        item["lon"] = (item["geometry"]["coordinates"][0][0] + item["geometry"]["coordinates"][1][0]) / 2
        item.pop("geometry", None)

        apply_category(Categories.FOOTWAY_CROSSING, item)

        if feature["CrosswalkType"] == "marked":
            item["extras"]["crossing:markings"] = "yes"
        elif feature["CrosswalkType"] == "unmarked":
            item["extras"]["crossing:markings"] = "no"

        if feature["Raised"] == "YES":
            item["extras"]["traffic_calming"] = "table"

        if feature["AreaRefuge"] == "YES":
            item["extras"]["crossing:island"] = "yes"
        elif feature["AreaRefuge"] == "NO":
            item["extras"]["crossing:island"] = "no"

        if feature["Signalized"] == "YES":
            item["extras"]["crossing:signals"] = "yes"
        elif feature["Signalized"] == "NO":
            item["extras"]["crossing:signals"] = "no"

        if feature["Illumination"] == "YES":
            item["extras"]["lit"] = "yes"
        elif feature["Illumination"] == "NO":
            item["extras"]["lit"] = "no"

        yield item
