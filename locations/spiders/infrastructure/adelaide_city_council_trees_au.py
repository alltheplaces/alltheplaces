from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AdelaideCityCouncilTreesAUSpider(ArcGISFeatureServerSpider):
    name = "adelaide_city_council_trees_au"
    item_attributes = {"operator": "Adelaide City Council", "operator_wikidata": "Q56477697", "state": "SA"}
    host = "services.arcgis.com"
    context_path = "BzylpWnjWP0tW4nL/ArcGIS"
    service_id = "Urban_Tree_Map___Genus_WFL1"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["Assetic_ID"])
        apply_category(Categories.NATURAL_TREE, item)
        genus = feature.get("Genus")
        species = feature.get("Species")
        if genus and species:
            item["extras"]["species"] = f"{genus} {species}"
            item["extras"]["genus"] = genus
        elif genus:
            item["extras"]["genus"] = genus
        if common_name := feature.get("Common_Name"):
            item["extras"]["taxon:en"] = common_name
        if height := feature.get("Height"):
            item["extras"]["height"] = f"{height}"
        item["extras"]["protected"] = "yes"
        yield item
