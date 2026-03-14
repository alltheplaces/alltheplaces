from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class PowercoZoneSubstationsNZSpider(ArcGISFeatureServerSpider):
    name = "powerco_zone_substations_nz"
    item_attributes = {"operator": "Powerco", "operator_wikidata": "Q7236675"}
    host = "services.arcgis.com"
    context_path = "VmeIOtXtktIhrOVG/ArcGIS"
    service_id = "Powerco_Zone_Substations_view"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["GlobalID"]
        item["name"] = feature["S_Name"].removesuffix(" Substation")
        apply_category(Categories.SUBSTATION_ZONE, item)
        yield item
