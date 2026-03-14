from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class RanchoCucamongaCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "rancho_cucamonga_city_council_trees_us"
    item_attributes = {
        "operator": "Rancho Cucamonga City Council",
        "operator_wikidata": "Q134606990",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "bF44QtfoYZDGo7TK/arcgis"
    service_id = "TreeInventory"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("AssetID")
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if botanical_name := feature.get("BotanicalName"):
            if "VACANT_SITE" in botanical_name.upper():
                return
            else:
                item["extras"]["species"] = botanical_name.strip()
        if common_name := feature.get("CommonName"):
            if "VACANT_SITE" in common_name.upper():
                return
            else:
                item["extras"]["taxon:en"] = common_name.strip()
        if dbh_ft := feature.get("DiameterBreastHieght"):
            item["extras"]["diameter"] = f"{dbh_ft}'"
        yield item
