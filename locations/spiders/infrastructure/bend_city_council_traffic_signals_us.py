from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BendCityCouncilTrafficSignalsUSSpider(ArcGISFeatureServerSpider):
    name = "bend_city_council_traffic_signals_us"
    item_attributes = {"operator": "Bend City Council", "operator_wikidata": "Q134540047", "state": "OR"}
    host = "services5.arcgis.com"
    context_path = "JisFYcK2mIVg9ueP/ArcGIS"
    service_id = "Traffic_Signals"
    layer_id = "6"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FacilityID"]
        item["name"] = feature["Intersection_Combined_Name"]
        apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        if alt_ref := feature.get("TSSU_ID"):
            item["extras"]["alt_ref"] = alt_ref

        if install_date_int := feature.get("Install_Date"):
            install_date = datetime.fromtimestamp(int(float(install_date_int) / 1000), UTC)
            if not install_date.isoformat().startswith("1900-01-01T"):
                item["extras"]["start_date"] = install_date.isoformat().split("T", 1)[0]
        yield item
