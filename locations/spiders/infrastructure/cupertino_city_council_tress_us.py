from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CupertinoCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "cupertino_city_council_trees_us"
    item_attributes = {
        "operator": "Cupertino City Council",
        "operator_wikidata": "Q134548005",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "gis.cupertino.org"
    context_path = "cupgis"
    service_id = "Public/AmazonData"
    layer_id = "29"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("Status") not in ["Active", "New Tree"]:
            return
        item["ref"] = feature.get("AssetID")
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature.get("Species")
        item["extras"]["taxon:en"] = feature.get("SpeciesCommonName")
        if dbh_in := feature.get("DiameterBreastHieght"):
            item["extras"]["diameter"] = f'{dbh_in}"'
        if height_ft := feature.get("Height"):
            item["extras"]["height"] = f"{height_ft}'"
        if dcrown_ft := feature.get("CanopyDiameter"):
            item["extras"]["diameter_crown"] = f"{dcrown_ft}'"
        yield item
