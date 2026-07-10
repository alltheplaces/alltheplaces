from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EdibleArrangementsUSSpider(JSONBlobSpider):
    name = "edible_arrangements_us"
    item_attributes = {"brand": "Edible Arrangements", "brand_wikidata": "Q5337996"}
    allowed_domains = ["www.ediblearrangements.com"]
    start_urls = ["https://www.ediblearrangements.com/api/stores/store-finder/get-stores?latitude=0&longitude=0"]
    locations_key = "storeData"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["website"] = urljoin("https://www.ediblearrangements.com/stores/", feature.get("pageFriendlyUrl"))
        oh = OpeningHours()
        for day_time in feature["timingsShort"]:
            day_time_text = " ".join(list(day_time.values()))
            oh.add_ranges_from_string(day_time_text)
        item["opening_hours"] = oh
        yield item
