import json
from typing import Iterable

from pyproj import Transformer
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WashingtonDotUSSpider(JSONBlobSpider):
    name = "washington_dot_us"
    item_attributes = {"operator": "Washington DOT", "operator_wikidata": "Q834834"}
    start_urls = ["https://data.wsdot.wa.gov/travelcenter/Cameras.json"]
    transformer = Transformer.from_crs("epsg:3857", "epsg:4326")

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = json.loads(response.text)
        assert json_data["spatialReference"]["latestWkid"] == 3857
        return json_data["features"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        info = feature["attributes"]
        item["ref"] = info["CameraID"]
        geometry = feature["geometry"]
        item["lat"], item["lon"] = self.transformer.transform(geometry["x"], geometry["y"])
        item["website"] = "https://wsdot.wa.gov/"
        item["image"] = info["ImageURL"]
        item["name"] = info["CameraTitle"]
        item["extras"]["camera:type"] = "fixed"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        # They serve up a few Oregon cameras which we filter out.
        if "wsdot" in item["image"]:
            # Only Washington state here.
            item["state"] = "WA"
            yield item
