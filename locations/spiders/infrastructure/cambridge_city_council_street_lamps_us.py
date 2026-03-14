from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CambridgeCityCouncilStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "cambridge_city_council_street_lamps_us"
    item_attributes = {"operator": "Cambridge City Council", "operator_wikidata": "Q133054988", "state": "MA"}
    host = "services1.arcgis.com"
    context_path = "WnzC35krSYGuYov4/ArcGIS"
    service_id = "Street_Lights"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["PoleID"]
        item.pop("street", None)
        if street_name := feature.get("StreetName"):
            if street_suffix := feature.get("StreetSuffix"):
                item["street_address"] = f"{street_name} {street_suffix}"
        apply_category(Categories.STREET_LAMP, item)
        yield item
