from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDublinTreesUSSpider(ArcGISFeatureServerSpider):
    name = "city_of_dublin_trees_us"
    item_attributes = {
        "operator": "City of Dublin",
        "operator_wikidata": "Q111367157",
        "state": "OH",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "NqY8dnPSEdMJhuRw/arcgis"
    service_id = "Street_Trees"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FacilityID"]
        item["street_address"] = feature["Address"]
        item.pop("addr_full", None)
        apply_category(Categories.NATURAL_TREE, item)
        if species := feature.get("Species"):
            item["extras"]["taxon:en"] = species
            if cultivar := feature.get("Cultivar"):
                item["extras"]["taxon:en"] = f"{species} '{cultivar}'"
        if dbh_ft := feature.get("DBH"):
            item["extras"]["diameter"] = f"{dbh_ft} '"
        yield item
