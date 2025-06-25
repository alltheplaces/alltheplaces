from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GlasgowCityCouncilStreetLampsGBSpider(ArcGISFeatureServerSpider):
    name = "glasgow_city_council_street_lamps_gb"
    item_attributes = {
        "operator": "Glasgow City Council",
        "operator_wikidata": "Q130637",
        "nsi_id": "N/A",
    }
    host = "utility.arcgis.com"
    context_path = "usrsvcs/servers/4d4122803b304cd3a80684a08d0a9143"
    service_id = "OPEN_DATA/Lighting_Columns"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.STREET_LAMP, item)
        yield item
