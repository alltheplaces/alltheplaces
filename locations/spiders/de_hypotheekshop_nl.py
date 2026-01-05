from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DeHypotheekshopNLSpider(JSONBlobSpider):
    name = "de_hypotheekshop_nl"
    item_attributes = {"brand": "De Hypotheekshop", "brand_wikidata": "Q124052986"}
    start_urls = ["https://www.hypotheekshop.nl/wp-json/vo/v1/establishments?per_page=500"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["website"] = feature.get("view_url")
        item["image"] = feature.get("image_general_url")

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("meet_times", []):
            for time in rule["times"]:
                item["opening_hours"].add_range(DAYS[rule["day"] - 1], time["from"], time["to"], time_format="%H:%M:%S")
        apply_category({"office": "mortgage"}, item)

        yield item
