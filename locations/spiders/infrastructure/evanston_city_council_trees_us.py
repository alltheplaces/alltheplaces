from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EvanstonCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "evanston_city_council_trees_us"
    item_attributes = {"operator": "Evanston City Council", "operator_wikidata": "Q138498023", "state": "IL"}
    host = "maps.cityofevanston.org"
    context_path = "arcgis"
    service_id = "OpenData/ArcGISOpenData"
    server_type = "MapServer"
    layer_id = "8"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("LifeCycle") != "Active Tree":
            return
        item["ref"] = feature["GlobalID"]
        item.pop("addr_full", None)
        item["housenumber"] = feature.get("Address")
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["genus"] = feature.get("Genus")
        if cultivar := feature.get("CULTIVAR", "").strip():
            item["extras"]["species"] = "{} {}".format(feature.get("SPP", "").strip(), cultivar)
        else:
            item["extras"]["species"] = feature.get("SPP")
        item["extras"]["taxon:en"] = feature.get("Common")
        if dbh_in := feature.get("DBH"):
            item["extras"]["diameter"] = f'{dbh_in}"'
        yield item
