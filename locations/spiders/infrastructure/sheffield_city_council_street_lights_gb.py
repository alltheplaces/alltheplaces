from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SheffieldCityCouncilStreetLightsGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_street_lights_gb"
    dataset_attributes = Licenses.GB_OGLv3.value | {"source": "api", "api": "arcgis"}
    item_attributes = {
        "operator": "Sheffield City Council",
        "operator_wikidata": "Q7492609",
        "nsi_id": "N/A",
    }
    host = "sheffieldcitycouncil.cloud.esriuk.com"
    context_path = "server"
    service_id = "AGOL/OpenData1"
    layer_id = "11"

    LAMP_MOUNT_MAPPING = {
        "SL: Hinged Column": {"lamp_mount": "straight_mast"},
        "SL: High Mast": {"lamp_mount": "high_mast"},
        "SL: Uplighter": {"lamp_mount": "ground", "support": "ground"},
        "SL: Wall Lamp": {"support": "wall_mounted"},
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.STREET_LAMP, item)
        if tags := self.LAMP_MOUNT_MAPPING.get(feature.get("featuretypename")):
            item["extras"].update(tags)
        yield item
