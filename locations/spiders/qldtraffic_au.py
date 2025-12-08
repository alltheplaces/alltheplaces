from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class QldtrafficAUSpider(JSONBlobSpider):
    name = "qldtraffic_au"
    item_attributes = {
        "operator": "Department of Transport and Main Roads",
        "operator_wikidata": "Q1191482",
        "nsi_id": "N/A",
    }
    allowed_domains = ["data.qldtraffic.qld.gov.au"]
    start_urls = [
        "https://data.qldtraffic.qld.gov.au/webcameras.geojson",
        "https://data.qldtraffic.qld.gov.au/floodcameras.geojson",
    ]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"])
        feature["name"] = feature.pop("description", None)
        feature["city"] = feature.pop("locality", None)
        feature["state"] = "QLD"
        # Geometry is supplied with projection of EPSG:4326 not EPSG:7844 as
        # the source data incorrectly states.
        feature["geometry"]["crs"]["properties"]["name"] = "EPSG:4326"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item.pop("website", None)
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        match str(feature["image_sourced_from"]).strip().upper():
            case "DOUGLAS SHIRE COUNCIL":
                item["operator"] = "Douglas Shire Council"
                item["operator_wikidata"] = "Q85372027"
            case "DEPARTMENT OF TRANSPORT & MAIN ROADS" | "DEPARTMENT OF TRANSPORT AND MAIN ROADS" | "NONE":
                # If not specified, it's likely the camera is operated by the
                # default operator "Department of Transport and Main Roads".
                pass
            case _:
                # If there is unknown operator specified then raise it as a
                # warning so this spider can be updated to include the
                # alternative operator.
                self.logger.warning("Unknown camera operator: {}".format(feature["image_sourced_from"]))
        item["extras"]["contact:webcam"] = feature["image_url"]
        item["extras"]["camera:type"] = "fixed"
        item["extras"]["camera:direction"] = (
            feature["direction"]
            .replace("NorthEast", "NE")
            .replace("NorthWest", "NW")
            .replace("North", "N")
            .replace("SouthEast", "SE")
            .replace("SouthWest", "SW")
            .replace("South", "S")
            .replace("East", "E")
            .replace("West", "W")
        )
        yield item
