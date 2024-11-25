from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.alltheplaces import AllThePlacesSpider


class SouthDakotaDotUSSpider(AllThePlacesSpider):
    name = "south_dakota_dot_us"
    item_attributes = {"operator": "South Dakota DOT", "operator_wikidata": "Q5570193"}
    start_urls = ["https://sd.cdn.iteris-atis.com/geojson/icons/metadata/icons.cameras.geojson"]

    def post_process_feature(
        self, item: Feature, source_feature: dict, response: Response, **kwargs
    ) -> Iterable[Feature]:
        extras = item.pop("extras")
        for info in extras["cameras"]:
            camera = item.deepcopy()
            camera["ref"] = source_feature["id"] + "-" + info["id"]
            camera["image"] = info["image"]
            camera["name"] = info["name"]
            camera["website"] = "https://www.sd511.org/"
            apply_category(Categories.SURVEILLANCE_CAMERA, camera)
            yield camera
