from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class SouthCarolinaUSSpider(JSONBlobSpider):
    name = "south_carolina_us"
    allowed_domains = ["sc.gov"]
    start_urls = ["https://sc.gov/google-maps-api/data"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["placeId"]
        item["name"] = feature["layerPlaceName"]
        item["street_address"] = clean_address([feature["address1"], feature["address2"]])
        item["city"] = feature["cityOrTown"]

        if feature["layerId"] == 31:  # STATE PARKS LAYER ID
            apply_category(Categories.LEISURE_PARK, item)
        else:
            apply_category({"office": "government"}, item)

        yield item
