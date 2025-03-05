from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SanFranciscoMtaTaxiRanksUSSpider(ArcGISFeatureServerSpider):
    name = "san_francisco_mta_taxi_ranks_us"
    item_attributes = {"operator": "San Francisco Municipal Transportation Agency", "operator_wikidata": "Q7414072", "state": "CA"}
    host = "services.sfmta.com"
    context_path = "arcgis"
    service_id = "DataSF/master"
    layer_id = "42"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("STATUS_1") != "Active":
            return
        item["ref"] = str(feature["TAXI_STOP_ID"])
        item["street_address"] = feature["ADDRESS"]
        item["city"] = feature["CITY_1"]
        item.pop("addr_full", None)
        item["image"] = feature["IMAGE"]
        apply_category(Categories.TAXI, item)
        if capacity := feature.get("CAPACITY"):
            item["extras"]["capacity"] = capacity
        yield item
