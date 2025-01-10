from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AlertcaliforniaUSSpider(JSONBlobSpider):
    name = "alertcalifornia_us"
    item_attributes = {"operator": "University of California, San Diego", "operator_wikidata": "Q622664"}
    allowed_domains = ["cameras.alertcalifornia.org"]
    start_urls = ["https://cameras.alertcalifornia.org/public-camera-data/all_cameras-v3.json"]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"])
        del feature["properties"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if coordinates := feature["geometry"].get("coordinates"):
            if coordinates[0] is None:
                # Unused (?) cameras appear to exist as cameras lacking coordinates
                return

            item["website"] = "https://cameras.alertcalifornia.org/?id={}".format(item["ref"])

            apply_category(Categories.SURVEILLANCE_CAMERA, item)

            # Azimuths can be changed over time so the camera direction is not
            # always a fixed/stable attribute. This extracted value for
            # panning cameras could possibly just be a centre of the field of
            # view the camera pans across.
            if direction := feature.get("az_current"):
                item["extras"]["camera:direction"] = str(direction)

            item["extras"]["contact:webcam"] = (
                "https://cameras.alertcalifornia.org/public-camera-data/{}/latest-frame.jpg".format(item["ref"])
            )

            yield item
