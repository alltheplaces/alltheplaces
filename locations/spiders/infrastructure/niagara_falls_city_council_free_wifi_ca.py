from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NiagaraFallsCityCouncilFreeWifiCASpider(ArcGISFeatureServerSpider):
    name = "niagara_falls_city_council_free_wifi_ca"
    item_attributes = {"operator": "Niagara Falls City Council", "operator_wikidata": "Q16941501", "state": "ON"}
    host = "services9.arcgis.com"
    context_path = "oMFQlUUrLd1Uh1bd/ArcGIS"
    service_id = "Niagara_Falls_Public_WiFi_Locations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        item["street_address"] = item.pop("addr_full", None)
        apply_category(Categories.ANTENNA, item)
        item["extras"]["internet_access"] = "wlan"
        item["extras"]["internet_access:fee"] = "no"
        yield item
