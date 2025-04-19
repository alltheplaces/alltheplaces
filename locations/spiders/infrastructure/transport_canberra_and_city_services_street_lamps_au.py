from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class TransportCanberraAndCityServicesStreetLampsAUSpider(ArcGISFeatureServerSpider):
    name = "transport_canberra_and_city_services_street_lamps_au"
    item_attributes = {
        "operator": "Transport Canberra & City Services",
        "operator_wikidata": "Q4650892",
        "state": "ACT",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "E5n4f1VY84i0xSjy/ArcGIS"
    service_id = "ACTGOV_Streetlight_Column_Assets"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("MAINTAINED_BY") != "RM - STREETLIGHTS":
            self.logger.warning("Street lamp has unknown maintainer: {}".format(feature["MAINTAINED_BY"]))
        item["ref"] = feature["ASSET_ID"]
        apply_category(Categories.STREET_LAMP, item)
        if feature.get("COLUMN_HEIGHT_UNIT") == "Metre" and feature.get("COLUMN_HEIGHT"):
            item["extras"]["height"] = "{} m".format(feature["COLUMN_HEIGHT"])
        yield item
