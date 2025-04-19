from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfOttawaTreesCASpider(ArcGISFeatureServerSpider):
    name = "city_of_ottawa_trees_ca"
    item_attributes = {"operator": "City of Ottawa", "operator_wikidata": "Q5123850", "state": "ON"}
    host = "maps.ottawa.ca"
    context_path = "arcgis"
    service_id = "Forestry"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["SAP_ID"]
        if street_name := feature.get("ADDSTR"):
            item["street"] = street_name
        if housenumber := feature.get("ADDNUM"):
            item["housenumber"] = housenumber
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if common_name := feature.get("SPECIES"):
            item["extras"]["taxon:en"] = common_name
        if dbh_cm := feature.get("DBH"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        yield item
