from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class QLDTrafficAUSpider(JSONBlobSpider):
    name = "qldtraffic_au"
    item_attributes = {
        "operator": "Queensland Government",
        "operator_wikidata": "Q3112627",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
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

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
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
