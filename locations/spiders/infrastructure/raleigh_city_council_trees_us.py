from typing import Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class RaleighCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "raleigh_city_council_trees_us"
    item_attributes = {
        "operator": "Raleigh City Council",
        "operator_wikidata": "Q7286898",
        "state": "NC",
        "nsi_id": "N/A",
    }
    host = "services.arcgis.com"
    context_path = "v400IkDOw1ad7Yad/ArcGIS"
    service_id = "PRCR_Urban_Forestry_Trees_Open_Data"
    layer_id = "0"
    _tree_code_mappings = {}

    def parse_layer_details(self, response: TextResponse) -> Iterable[JsonRequest]:
        fields = response.json()["fields"]
        for field in fields:
            if field["name"] == "SPP_CODE":
                for coded_value in field["domain"]["codedValues"]:
                    self._tree_code_mappings[coded_value["code"]] = coded_value["name"]
        yield from super().parse_layer_details(response)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["GlobalID"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if species_code := feature.get("SPP_CODE"):
            if species_code in self._tree_code_mappings.keys():
                item["extras"]["taxon:en"] = self._tree_code_mappings[species_code]
        if dbh_in := feature.get("DIAMETER"):
            item["extras"]["diameter"] = f'{dbh_in}"'
        yield item
