from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class TranspowerSubstationsNZSpider(ArcGISFeatureServerSpider):
    name = "transpower_substations_nz"
    item_attributes = {"operator": "Transpower New Zealand", "operator_wikidata": "Q7835339"}
    host = "services3.arcgis.com"
    context_path = "AkUq3zcWf7TVqyR9/ArcGIS"
    service_id = "Sites"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["type"] in ["TEE"]:
            return
        if feature["type"] not in ["ACSTN", "HVDC"]:
            self.logger.warning("Unknown site type: {}".format(feature["type"]))
            return
        item["ref"] = feature["MXLOCATION"]
        item["name"] = feature["description"]
        apply_category(Categories.SUBSTATION_TRANSMISSION, item)
        yield item
