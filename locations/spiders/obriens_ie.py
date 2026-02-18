from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class ObriensIESpider(JSONBlobSpider):
    name = "obriens_ie"
    item_attributes = {"brand": "O'Briens", "brand_wikidata": "Q113151266"}
    start_urls = ["https://adminob.iplanit.ie/api/getLocationsInventory"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        oh = OpeningHours()
        oh.add_ranges_from_string(feature["openingHours"])
        item["opening_hours"] = oh
        yield item
