from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BoroondaraCityCouncilTreesAUSpider(ArcGISFeatureServerSpider):
    name = "boroondara_city_council_trees_au"
    item_attributes = {"operator": "Boroondara City Council", "operator_wikidata": "Q56477791", "state": "VIC"}
    host = "services6.arcgis.com"
    context_path = "773swFbKnmOvqBdL/ArcGIS"
    service_id = "Conquest_Trees_view"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("Status") != "Existing":
            # Ignore "disposed"/removed trees (including sites that are
            # planned to have a tree planted, but don't currently have a
            # planted tree).
            return
        item["ref"] = str(feature["AssetID"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if description := feature.get("AssetDescription"):
            if len(description.split(" - ")) != 0:
                item["extras"]["species"] = description.split(" - ")[-1]
        if planted_date := feature.get("DatePlanted"):
            planted_date_parts = planted_date.split("/")
            item["extras"]["start_date"] = "{}-{}-{}".format(planted_date_parts[2], planted_date_parts[1], planted_date_parts[0])
        yield item
