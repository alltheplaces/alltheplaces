from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AlertcaliforniaUSSPider(JSONBlobSpider):
    name = "alertcalifornia_us"
    item_attributes = {"operator": "University of California, San Diego", "operator_wikidata": "Q622664"}
    allowed_domains = ["cameras.alertcalifornia.org"]
    start_urls = ["https://cameras.alertcalifornia.org/public-camera-data/all_cameras-v3.json"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for camera in response.json()["features"]:
            if coordinates := camera["geometry"].get("coordinates"):
                if coordinates[0] is None:
                    # Unused (?) cameras appear to exist as cameras lacking coordinates
                    continue

            properties = {
                "ref": camera["properties"]["id"],
                "name": camera["properties"]["name"],
                "geometry": camera["geometry"],
                "website": "https://cameras.alertcalifornia.org/?id={}".format(camera["properties"]["id"]),
            }

            apply_category(Categories.SURVEILLANCE_CAMERA, properties)

            # Azimuths can be changed over time so the camera direction is not
            # always a fixed/stable attribute. This extracted value for
            # panning cameras could possibly just be a centre of the field of
            # view the camera pans across.
            if direction := camera["properties"].get("az_current"):
                properties["extras"]["camera:direction"] = str(direction)

            properties["extras"]["contact:webcam"] = (
                "https://cameras.alertcalifornia.org/public-camera-data/{}/latest-frame.jpg".format(properties["ref"])
            )

            yield Feature(**properties)
