from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfSydneyTreesAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_sydney_trees_au"
    item_attributes = {"operator": "City of Sydney", "operator_wikidata": "Q56477532", "state": "NSW"}
    host = "services1.arcgis.com"
    context_path = "cNVyNtjGVZybOQWZ/ArcGIS"
    service_id = "Trees"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["asset_id"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature.get("SpeciesName")
        item["extras"]["taxon:en"] = feature.get("CommonName")
        if height_m := feature.get("TreeHeight"):
            item["extras"]["height"] = f"{height_m} m"
        if dbh_cm := feature.get("DBH_in_cm"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        if crown_width_m := feature.get("TreeCanopyNS"):
            item["extras"]["diameter_crown"] = f"{crown_width_m} m"
        yield item
