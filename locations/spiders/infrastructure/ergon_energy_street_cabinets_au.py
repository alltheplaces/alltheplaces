from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class ErgonEnergyStreetCabinetsAUSpider(ArcGISFeatureServerSpider):
    name = "ergon_energy_street_cabinets_au"
    item_attributes = {"operator": "Ergon Energy", "operator_wikidata": "Q5385825"}
    host = "services.arcgis.com"
    context_path = "33eHbTVqo7gtiCE8/ArcGIS"
    service_id = "Structures_Ergon"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["SITE_LABEL"]
        item["state"] = "QLD"
        apply_category(Categories.STREET_CABINET_POWER, item)
        yield item
