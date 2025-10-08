from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDarwinCctvAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_darwin_cctv_au"
    item_attributes = {"operator": "City of Darwin", "operator_wikidata": "Q125673118"}
    host = "services6.arcgis.com"
    context_path = "tVfesLETUHNU9Vna/ArcGIS"
    service_id = "CCTV_Points"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["CameraID"]:
            # Invalid cameras are in this dataset and have no reference number
            # assigned. These cameras are observed to have coordinates in the
            # ocean. Ignore these cameras.
            return

        item["ref"] = feature["CameraID"]
        item["name"] = feature["Description"]
        item["state"] = "NT"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        item["extras"]["surveillance"] = "public"

        if feature["Camera_Type"] != "Fixed":
            self.logger.warning("Unknown camera type: {}".format(feature["Camera_Type"]))
        else:
            item["extras"]["camera:type"] = "fixed"
            if feature["Direction"]:
                direction_angle = int(feature["Direction"])
                if direction_angle < 0:
                    direction_angle = 360 + direction_angle
                item["extras"]["camera:direction"] = str(direction_angle)

        yield item
