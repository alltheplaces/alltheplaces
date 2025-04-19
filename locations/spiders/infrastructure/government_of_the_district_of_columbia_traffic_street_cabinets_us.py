from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GovernmentOfTheDistrictOfColumbiaTrafficStreetCabinetsUSSpider(ArcGISFeatureServerSpider):
    name = "government_of_the_district_of_columbia_traffic_street_cabinets_us"
    item_attributes = {"operator": "Government of the District of Columbia", "operator_wikidata": "Q16152667", "state": "DC"}
    host = "maps2.dcgis.dc.gov"
    context_path = "dcgis"
    service_id = "DCGIS_DATA/Transportation_Signs_Signals_Lights_WebMercator"
    server_type = "MapServer"
    layer_id = "27"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["CABINETID"])
        apply_category(Categories.STREET_CABINET_TRAFFIC_CONTROL, item)
        yield item

