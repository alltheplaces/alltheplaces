from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EnergexStreetCabinetsAUSpider(ArcGISFeatureServerSpider):
    name = "energex_street_cabinets_au"
    item_attributes = {"operator": "Energex", "operator_wikidata": "Q5376841"}
    host = "services.arcgis.com"
    context_path = "bfVzktoY0OhzQCDj/ArcGIS"
    service_id = "Network_Energex"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["SITE_REF"]
        item["state"] = "QLD"
        apply_category(Categories.STREET_CABINET_POWER, item)
        yield item
