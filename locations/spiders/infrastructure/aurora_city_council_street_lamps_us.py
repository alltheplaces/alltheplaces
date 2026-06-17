from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuroraCityCouncilStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "aurora_city_council_street_lamps_us"
    item_attributes = {"operator": "Aurora City Council", "operator_wikidata": "Q138498688", "state": "CO"}
    host = "services3.arcgis.com"
    context_path = "0Va1ID99NSrNyyPX/arcgis"
    service_id = "Lighting_Assets_City_Owned_view"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if asset_id := feature["STREET_LIGHT_ID"]:
            item["ref"] = asset_id
        else:
            item["ref"] = feature["GlobalID"]
        apply_category(Categories.STREET_LAMP, item)
        yield item
