import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class VermontElectricCooperativeSubstationsUSSpider(ArcGISFeatureServerSpider):
    name = "vermont_electric_cooperative_substations_us"
    item_attributes = {"operator": "Vermont Electric Cooperative", "operator_wikidata": "Q7921713", "state": "VT", "nsi_id": "N/A"}
    host = "services6.arcgis.com"
    context_path = "xcyrEMQ4nxKC9P7Y/ArcGIS"
    service_id = "VEC_Online_Viewer"
    layer_id = "2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["gs_station_number"]
        item["name"] = re.sub(r"^\d+ ", "", feature["gs_name"])
        apply_category(Categories.SUBSTATION, item)
        yield item
