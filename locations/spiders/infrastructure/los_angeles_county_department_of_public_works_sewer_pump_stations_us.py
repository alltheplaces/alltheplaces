from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LosAngelesCountyDepartmentOfPublicWorksSewerPumpStationsUSSpider(ArcGISFeatureServerSpider):
    name = "los_angeles_county_department_of_public_works_sewer_pump_stations_us"
    item_attributes = {
        "operator": "Los Angeles County Department of Public Works",
        "operator_wikidata": "Q6682081",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "dpw.gis.lacounty.gov"
    context_path = "dpw"
    service_id = "Sanitary_Sewer_Network"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["CW_ASSETID"]
        item["name"] = feature["PUMP_STATION_NAME"]
        apply_category(Categories.PUMPING_STATION_SEWAGE, item)
        yield item
