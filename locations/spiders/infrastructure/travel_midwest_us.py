from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TravelMidwestUSSpider(JSONBlobSpider):
    name = "travel_midwest_us"
    item_attributes = {"nsi_id": "N/A"}
    allowed_domains = ["travelmidwest.com"]
    start_urls = ["https://travelmidwest.com/lmiga/cameraMap.json"]
    locations_key = "features"

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {"bbox": [-90, -180, 90, 180]}
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["properties"]["dis"]:
            # Camera disabled/unused and should be ignored.
            return

        match feature["properties"]["src"]:
            case "DuPage County":
                # Camera from DuPage County, Illinois.
                item["operator"] = "DuPage County Division of Transportation"
                item["operator_wikidata"] = "Q132853083"
                item["state"] = "IL"
            case "IDOT D1 Camera" | "IDOT D4":
                # Camera from state of Illinois.
                item["operator"] = "Illinois Department of Transportation"
                item["operator_wikidata"] = "Q4925114"
                item["state"] = "IL"
            case "Illinois Tollway":
                item["operator"] = "Illinois State Toll Highway Authority"
                item["operator_wikidata"] = "Q1071617"
                item["state"] = "IL"
            case "InDOT":
                # Camera from state of Indiana.
                item["operator"] = "Indiana Department of Transportation"
                item["operator_wikidata"] = "Q4925393"
                item["state"] = "IN"
            case "IowaDOT":
                # Camera from state of Iowa.
                item["operator"] = "Iowa Department of Transportation"
                item["operator_wikidata"] = "Q4925621"
                item["state"] = "IA"
            case "KYTC":
                # Camera from state of Kentucky.
                item["operator"] = "Kentucky Transportation Cabinet"
                item["operator_wikidata"] = "Q4926022"
                item["state"] = "KY"
            case "Lake County":
                # Camera from Lake County, Illinois.
                item["operator"] = "Lake County Division of Transportation"
                item["operator_wikidata"] = "Q132853117"
                item["state"] = "IL"
            case "WisDOT":
                # Camera from state of Wisconsin.
                item["operator"] = "Wisconsin Department of Transportation"
                item["operator_wikidata"] = "Q8027162"
                item["state"] = "WI"
            case _:
                raise ValueError("Unknown source transportation department: {}".format(feature["properties"]["src"]))

        item["ref"] = feature["properties"]["id"]
        item["name"] = feature["properties"]["locDesc"]
        item["geometry"] = feature["geometry"]
        if len(feature["properties"]["remUrls"]) > 1:
            item["extras"]["camera:type"] = "dome"
        else:
            item["extras"]["camera:type"] = "fixed"
        item["extras"]["contact:webcam"] = ";".join(feature["properties"]["remUrls"])
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        yield item
