from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class VicFreeWifiAUSpider(ArcGISFeatureServerSpider):
    name = "vic_free_wifi_au"
    item_attributes = {"operator": "Victorian State Government", "operator_wikidata": "Q5589335"}
    host = "services-ap1.arcgis.com"
    context_path = "qP7JqzPTuwJlaCRD/ArcGIS"
    service_id = "vicfreewifi"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Name"]
        item["name"] = feature["Long_Name"].removeprefix(item["ref"]).strip("-")
        item["addr_full"] = feature["Location_details"]
        apply_category(Categories.ANTENNA, item)
        item["extras"]["internet_access"] = "wlan"
        item["extras"]["internet_access:fee"] = "no"
        item["extras"]["internet_access:operator"] = "TPG Telecom"
        item["extras"]["internet_access:operator:wikidata"] = "Q7939276"
        item["extras"]["internet_access:ssid"] = "VicFreeWiFi"
        yield item
