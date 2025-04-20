from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class TranspowerPolesNZSpider(ArcGISFeatureServerSpider):
    name = "transpower_poles_nz"
    item_attributes = {"operator": "Transpower", "operator_wikidata": "Q7835339"}
    host = "services3.arcgis.com"
    context_path = "AkUq3zcWf7TVqyR9/ArcGIS"
    service_id = "Structures"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["MXLOCATION"]
        if feature["LongType"].strip().endswith(" Pole"):
            apply_category(Categories.POWER_POLE, item)
        elif feature["LongType"].strip().endswith(" Tower"):
            apply_category(Categories.POWER_TOWER, item)
        elif feature["LongType"].strip() in ["Terminal", "Termination", "Unknown"]:
            apply_category(Categories.POWER_POLE, item)
        else:
            self.logger.warning("Unknown structure type: {}".format(feature["LongType"]))
        yield item
