from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KentuckyTransportationCabinetUSSpider(JSONBlobSpider):
    name = "kentucky_transportation_cabinet_us"
    item_attributes = {"operator": "Kentucky Transportation Cabinet", "operator_wikidata": "Q4926022", "state": "KY", "extras": Categories.SURVEILLANCE_CAMERA.value}
    allowed_domains = ["services2.arcgis.com"]
    start_urls = ["https://services2.arcgis.com/CcI36Pduqd0OR4W9/ArcGIS/rest/services/trafficCamerasCur_Prd/FeatureServer/0/query?where=1%3D1&outFields=OBJECTID%2Cdescription%2Csnapshot%2Clatitude%2Clongitude&f=pjson"]
    locations_key = "features"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["attributes"]["OBJECTID"]
        item["name"] = feature["attributes"]["description"]
        item["lat"] = feature["geometry"]["y"]
        item["lon"] = feature["geometry"]["x"]
        item["extras"]["contact:webcam"] = feature["attributes"]["snapshot"]
        item["extras"]["camera:type"] = "fixed"
        yield item
