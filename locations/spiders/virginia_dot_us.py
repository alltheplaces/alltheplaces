from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.alltheplaces import AllThePlacesSpider


class VirginiaDotUSSpider(AllThePlacesSpider):
    name = "virginia_dot_us"
    item_attributes = {"operator": "Virginia DOT", "operator_wikidata": "Q7934247"}
    start_urls = ["https://511.vdot.virginia.gov/services/map/layers/map/cams"]

    def post_process_feature(
        self, item: Feature, source_feature: dict, response: Response, **kwargs
    ) -> Iterable[Feature]:
        extras = item.pop("extras")
        item["image"] = extras["image_url"]
        item["ref"] = extras["id"]
        name = item["name"] = extras["description"]
        item["website"] = "https://511.vdot.virginia.gov"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        # A handful of cameras are out of state.
        if "West Virginia" not in name and "Tennessee" not in name:
            item["state"] = "VT"
            yield item
