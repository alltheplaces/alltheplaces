import re
from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NationalParksBoardTreesSGSpider(ArcGISFeatureServerSpider):
    name = "national_parks_board_trees_sg"
    item_attributes = {"operator": "National Parks Board", "operator_wikidata": "Q6974762"}
    host = "services6.arcgis.com"
    context_path = "s5gdswleLl0QthYa/ArcGIS"
    service_id = "TreeInformation_Hashing"
    layer_id = "0"

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url="https://www.nparks.gov.sg/ptmapi/TokenAuthApi/GetAuthToken", callback=self.parse_token)

    def parse_token(self, response: Response) -> Iterable[JsonRequest]:
        self.additional_parameters = {"token": response.json()["ViewToken"]}
        yield from super().start_requests()

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Public_treeid"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature["SPSC_NM"]

        if dbh_m := feature.get("GRTH_SIZE"):
            item["extras"]["diameter"] = f"{dbh_m} m"

        if height_range_m := feature.get("HEIGHT"):
            height_range_m = height_range_m.strip()
            if m := re.match(r">(\d+) but ≤(\d+)", height_range_m):
                height_min = m.group(1)
                height_max = m.group(2)
                item["extras"]["height:range"] = f"{height_min}-{height_max} m"
            elif m := re.match(r"(\d+)\s*-\s*(\d+)", height_range_m):
                height_min = m.group(1)
                height_max = m.group(2)
                item["extras"]["height:range"] = f"{height_min}-{height_max} m"
            elif m := re.match(r"(?:[<≤]|<=)(\d+)", height_range_m):
                height_max = m.group(1)
                item["extras"]["height:range"] = f"0-{height_max} m"
            elif m := re.match(r">(\d+)", height_range_m):
                height_min = m.group(1)
                item["extras"]["height"] = f"{height_min} m"
            elif height_range_m.startswith("-"):
                # Unknown height range listed as -1. Ignore.
                pass
            else:
                self.logger.warning("Unknown height range format: {}".format(height_range_m))

        yield item
