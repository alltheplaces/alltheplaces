from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SanFranciscoMtaBicycleParkingUSSpider(ArcGISFeatureServerSpider):
    name = "san_francisco_mta_bicycle_parking_us"
    item_attributes = {
        "operator": "San Francisco Municipal Transportation Agency",
        "operator_wikidata": "Q7414072",
        "state": "CA",
    }
    host = "services.sfmta.com"
    context_path = "arcgis"
    service_id = "DataSF/master"
    layer_id = "32"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        item.pop("street", None)
        item["street_address"] = item.pop("addr_full", None)
        apply_category(Categories.BICYCLE_PARKING, item)
        if capacity := feature.get("SPACES"):
            item["extras"]["capacity"] = capacity
        if rack_count := feature.get("RACKS"):
            item["extras"]["bicycle_parking"] = "rack"
        if installation_year := feature.get("INSTALL_YR"):
            if installation_month := feature.get("INSTALL_MO"):
                item["extras"]["start_date"] = "{}-{}".format(installation_year, str(installation_month).zfill(2))
        yield item
