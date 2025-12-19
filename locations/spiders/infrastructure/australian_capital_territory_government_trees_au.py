from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AustralianCapitalTerritoryGovernmentTreesAUSpider(ArcGISFeatureServerSpider):
    name = "australian_capital_territory_government_trees_au"
    item_attributes = {"state": "ACT", "nsi_id": "N/A"}
    host = "services1.arcgis.com"
    context_path = "E5n4f1VY84i0xSjy/ArcGIS"
    service_id = "ACTGOV_Tree_Assets"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["ASSET_ID"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if species := feature.get("BOTANICAL_NAME"):
            item["extras"]["species"] = species
        if genus := feature.get("GENUS"):
            item["extras"]["genus"] = genus
        match feature.get("OWNERSHIP"):
            case "URBAN TREESCAPES":
                item["operator"] = "Transport Canberra & City Services"
                item["operator_wikidata"] = "Q4650892"
            case "PARKS AND CONSERVATION SERVICE":
                item["operator"] = "ACT Parks and Conservation Service"
                item["operator_wikidata"] = "Q111082423"
            case _:
                self.logger.warning("Unknown operator: {}".format(feature.get("MAINTAINED_BY")))
        yield item
