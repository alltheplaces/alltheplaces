from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.alltheplaces import AllThePlacesSpider


class NorthDakotaDotUSSpider(AllThePlacesSpider):
    name = "north_dakota_dot_us"
    # TODO: this hits amenity=payment_terminal in NSI!
    # item_attributes = {"operator": "North Dakota DOT", "operator_wikidata": "Q5569030"}
    start_urls = ["https://travelfiles.dot.nd.gov/geojson/cameras/1732123545043/cameras.json"]

    def post_process_feature(
        self, item: Feature, source_feature: dict, response: Response, **kwargs
    ) -> Iterable[Feature]:
        extras = item.pop("extras")
        synthetic_id = 0
        for info in extras["Cameras"]:
            camera = item.deepcopy()
            synthetic_id += 1
            camera["ref"] = source_feature["id"] + "-" + str(synthetic_id)
            camera["image"] = info["FullPath"]
            if not info.get("Direction"):
                camera["name"] = "Traffic camera"
            else:
                camera["name"] = "Camera " + info["Direction"]
            camera["website"] = "https://travel.dot.nd.gov/"
            camera["state"] = "ND"
            apply_category(Categories.SURVEILLANCE_CAMERA, camera)
            yield camera
