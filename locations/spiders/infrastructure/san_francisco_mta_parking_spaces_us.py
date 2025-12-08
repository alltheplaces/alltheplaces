from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SanFranciscoMtaParkingSpacesUSSpider(ArcGISFeatureServerSpider):
    name = "san_francisco_mta_parking_spaces_us"
    item_attributes = {
        "operator": "San Francisco Municipal Transportation Agency",
        "operator_wikidata": "Q7414072",
        "state": "CA",
    }
    host = "services.sfmta.com"
    context_path = "arcgis"
    service_id = "DataSF/master"
    layer_id = "19"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["POST_ID"])
        item["housenumber"] = str(feature["STREET_NUM"])
        apply_category(Categories.PARKING_SPACE, item)
        yield item
