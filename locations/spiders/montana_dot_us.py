from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.alltheplaces import AllThePlacesSpider


# Very similar to South Caroline DOT, but pulls in some cameras surrounding the state!
class MontanaDotUSSpider(AllThePlacesSpider):
    name = "montana_dot_us"
    start_urls = ["https://mt.cdn.iteris-atis.com/geojson/icons/metadata/icons.rwis.geojson"]

    def post_process_feature(
        self, item: Feature, source_feature: dict, response: Response, **kwargs
    ) -> Iterable[Feature]:
        extras = item.pop("extras")
        item["ref"] = extras["id"]
        camera = extras["cameras"][0]
        name = item["name"] = camera["description"]
        item["image"] = camera["image"]

        if "canada" in name.lower():
            item["country"] = "CA"
        else:
            item["country"] = "US"
            state = name[-2:]
            if state in ["ND", "SD", "WY", "ID"]:
                item["state"] = state
            else:
                item["state"] = "MT"
                item["operator"] = "Montana DOT"
                item["operator_wikidata"] = "Q5558259"
                item["website"] = "https://www.511mt.net/"

        apply_category(Categories.SURVEILLANCE_CAMERA, item)

        yield item
