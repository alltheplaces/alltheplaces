import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class YorkRegionalCouncilTreesCASpider(ArcGISFeatureServerSpider):
    name = "york_regional_council_trees_ca"
    item_attributes = {"operator": "York Regional Council", "operator_wikidata": "Q8055526", "state": "ON"}
    host = "ww8.yorkmaps.ca"
    context_path = "arcgis"
    service_id = "OpenData/Biodiversity"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["TREEID"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if species := feature.get("SPECIES"):
            item["extras"]["species"] = species
        if common_name := feature.get("COMMONNAME"):
            item["extras"]["taxon:en"] = common_name
        if planting_year := feature.get("YEARPLANTED"):
            item["extras"]["start_date"] = str(planting_year)
        if dbh_cm := feature.get("CURRENTDBH"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        if tree_height_m := feature.get("TREEHEIGHT"):
            if m := re.fullmatch(r"(\d+) - (\d+) metres", tree_height_m):
                min_height_m = m.group(1)
                max_height_m = m.group(2)
                item["extras"]["height_range"] = f"{min_height_m}-{max_height_m} m"
            elif m := re.fullmatch(r"(\d+)\+ metres", tree_height_m):
                min_height_m = m.group(1)
                item["extras"]["height"] = f"{min_height_m} m"
            else:
                self.logger.warning(f"Unknown/unhandled tree height format encountered: {tree_height_m}")
        yield item
