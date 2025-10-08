from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfCanningTreesAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_canning_trees_au"
    item_attributes = {"operator": "City of Canning", "operator_wikidata": "Q56477868", "state": "WA"}
    host = "services-ap1.arcgis.com"
    context_path = "rpSo5yFb78UOvPOG/ArcGIS"
    service_id = "GreenSpace_Public_View"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("Tree_Status") != "Planted" or feature.get("Botanic_Name") == "To be selected":
            # Ignore planned tree plantings.
            return
        item["ref"] = feature["GlobalID"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["alt_ref"] = feature["Tree_id"]  # Not unique, appears to be a site/area ID.
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature.get("Botanic_Name")
        item["extras"]["genus"] = feature.get("Genus")
        item["extras"]["taxon:en"] = feature.get("Common_Name")
        if planted_year := feature.get("Year_int"):
            item["extras"]["start_date"] = str(planted_year)
        yield item
