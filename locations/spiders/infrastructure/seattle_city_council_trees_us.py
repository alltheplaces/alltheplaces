from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_city_council_trees_us"
    item_attributes = {"nsi_id": "N/A"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Combined_Tree_Point"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        match feature.get("OWNERSHIP"):
            case "Other" | "Private":
                return
            case "King County":
                item["operator"] = "King County Council"
                item["operator_wikidata"] = "Q6411382"
            case "Port of Seattle":
                item["operator"] = "Port of Seattle"
                item["operator_wikidata"] = "Q7231262"
            case "Seattle Center":
                item["operator"] = "Seattle Center Foundation"
                item["operator_wikidata"] = "Q30268396"
            case "Seattle City Light":
                item["operator"] = "Seattle City Light"
                item["operator_wikidata"] = "Q7442080"
            case "Seattle Department of Transportation":
                item["operator"] = "Seattle Department of Transportation"
                item["operator_wikidata"] = "Q39052410"
            case "Seattle Fleets and Administrative Services":
                item["operator"] = "Seattle City Council"
                item["operator_wikidata"] = "Q7442079"
            case "Seattle Housing Authority":
                item["operator"] = "Seattle Housing Authority"
                item["operator_wikidata"] = "Q7442112"
            case "Seattle Parks and Recreation":
                item["operator"] = "Seattle Parks and Recreation"
                item["operator_wikidata"] = "Q7442147"
            case "Seattle Public Schools":
                item["operator"] = "Seattle Public Schools"
                item["operator_wikidata"] = "Q3236113"
            case "Seattle Public Utilities":
                item["operator"] = "Seattle Public Utilities"
                item["operator_wikidata"] = "Q7442159"
            case "Sound Transit":
                item["operator"] = "Sound Transit"
                item["operator_wikidata"] = "Q3965367"
            case "Washington State Department of Transportation":
                item["operator"] = "Washington State Department of Transportation"
                item["operator_wikidata"] = "Q834834"
            case _:
                self.logger.warning("Unknown tree owner: {}".format(feature["OWNERSHIP"]))
        item["ref"] = feature.get("PEST_UNIT_ID")
        item["street_address"] = feature.get("UNITDESC")
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature.get("SCIENTIFIC_NAME")
        item["extras"]["taxon:en"] = feature.get("COMMON_NAME")
        if dbh_in := feature.get("dbh"):
            item["extras"]["diameter"] = f'{dbh_in}"'
        yield item
