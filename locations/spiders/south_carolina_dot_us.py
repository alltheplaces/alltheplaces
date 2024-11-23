from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.alltheplaces import AllThePlacesSpider


class SouthCarolinaDotUSSpider(AllThePlacesSpider):
    name = "south_carolina_dot_us"
    item_attributes = {
        "operator": "South Carolina DOT",
        "operator_wikidata": "Q5569993",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://sc.cdn.iteris-atis.com/geojson/icons/metadata/icons.cameras.geojson"]

    def post_process_feature(
        self, item: Feature, source_feature: dict, response: Response, **kwargs
    ) -> Iterable[Feature]:
        extras = item.pop("extras")
        item["image"] = extras["image_url"]
        item["ref"] = item["name"]
        item["name"] = extras["description"]
        item["website"] = "https://www.511sc.org/"
        yield item
