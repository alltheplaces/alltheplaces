from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CambridgeCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "cambridge_city_council_trees_us"
    item_attributes = {"operator": "Cambridge City Council", "operator_wikidata": "Q133054988", "state": "MA"}
    host = "services1.arcgis.com"
    context_path = "WnzC35krSYGuYov4/ArcGIS"
    service_id = "Trees"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("SiteType") != "Tree":
            return
        item["ref"] = feature["GlobalID"]
        if street_number := feature.get("StreetNumber"):
            item["housenumber"] = str(street_number)
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature["ScientificName"]
        item["extras"]["genus"] = feature["Genus"]
        item["extras"]["taxon:en"] = feature["CommonName"]
        if dbh_in := feature.get("diameter"):
            item["extras"]["diameter"] = f"{dbh_in} in"
        item["extras"]["protected"] = "yes"
        yield item
