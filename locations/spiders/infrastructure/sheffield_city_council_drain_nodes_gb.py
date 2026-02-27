from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

# https://sheffield-city-council-open-data-sheffieldcc.hub.arcgis.com/datasets/0a380126e8f14d318e52b7129269c80e_3/explore


class SheffieldCityCouncilDrainNodesGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_drain_nodes_gb"
    dataset_attributes = ArcGISFeatureServerSpider.dataset_attributes | Licenses.GB_OGLv3.value
    item_attributes = {
        "operator": "Sheffield City Council",
        "operator_wikidata": "Q7492609",
        "nsi_id": "N/A",
    }
    host = "sheffieldcitycouncil.cloud.esriuk.com"
    context_path = "server"
    service_id = "AGOL/OpenData_FloodAndWaterManagement"
    server_type = "MapServer"
    layer_id = "3"

    TYPE_CATEGORY_MAPPING = {
        "GY": Categories.KERB_GRATE,  # Gully
        "GULY": Categories.KERB_GRATE,  # Gully
        "CP": Categories.MANHOLE,  # Catchpit
        "MH": Categories.MANHOLE,  # Manhole
        "IC": Categories.MANHOLE,  # Inspection chamber
        "OUTF": Categories.OUTFALL_STORMWATER,  # Outfall
        "PS": Categories.PUMPING_STATION_STORMWATER,  # Pumping station
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if category := self.TYPE_CATEGORY_MAPPING.get(feature.get("type")):
            item["ref"] = str(feature["id"])
            apply_category(category, item)
            yield item
