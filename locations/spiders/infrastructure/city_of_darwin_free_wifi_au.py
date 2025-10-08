from json import loads
from typing import Iterable

from scrapy.http import Response
from shapely import to_geojson
from shapely.geometry import Polygon, shape

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDarwinFreeWifiAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_darwin_free_wifi_au"
    item_attributes = {"operator": "City of Darwin", "operator_wikidata": "Q125673118"}
    host = "services6.arcgis.com"
    context_path = "tVfesLETUHNU9Vna/ArcGIS"
    service_id = "Public_Wifi_APs_and_Coverage"
    layer_id = "5"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        item["geometry"] = loads(to_geojson(Polygon(shape(feature["geometry"])).centroid))
        item["state"] = "NT"
        apply_category(Categories.ANTENNA, item)
        item["extras"]["internet_access"] = "wlan"
        item["extras"]["internet_access:fee"] = "no"
        item["extras"]["internet_access:operator"] = "Telstra"
        item["extras"]["internet_access:operator:wikidata"] = "Q721162"
        item["extras"]["internet_access:ssid"] = "City of Darwin Free Wi-Fi"
        yield item
