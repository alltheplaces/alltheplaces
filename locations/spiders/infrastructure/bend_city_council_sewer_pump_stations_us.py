from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BendCityCouncilSewerPumpStationsUSSpider(ArcGISFeatureServerSpider):
    name = "bend_city_council_sewer_pump_stations_us"
    item_attributes = {"operator": "Bend City Council", "operator_wikidata": "Q134540047", "state": "OR"}
    host = "services5.arcgis.com"
    context_path = "JisFYcK2mIVg9ueP/ArcGIS"
    service_id = "Lift_Station"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("LifecycleStatus") != "I":
            # Decommissioned, inactive/abandoned or proposed pump stations
            # should be ignored.
            return

        item["ref"] = feature["FacilityID"]
        item["name"] = feature["LiftStationID"]

        apply_category(Categories.PUMPING_STATION_SEWAGE, item)

        if install_date_int := feature.get("InstallDate"):
            install_date = datetime.fromtimestamp(int(float(install_date_int) / 1000), UTC)
            if not install_date.isoformat().startswith("1900-01-01T"):
                item["extras"]["start_date"] = install_date.isoformat().split("T", 1)[0]

        yield item
