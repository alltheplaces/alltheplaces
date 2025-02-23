from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CuraleafUSSpider(JSONBlobSpider):
    name = "curaleaf_us"
    item_attributes = {"brand": "Curaleaf", "brand_wikidata": "Q85754829"}
    allowed_domains = ["curaleaf.com"]
    start_urls = ["https://curaleaf.com/api/dispensaries/store-drawer"]
    locations_key = "data"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("location"))
        feature["street_address"] = feature.pop("address")
        feature["state"] = feature["state"]["abbreviation"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["uid"]
        item["branch"] = feature["friendlyName"]
        item["website"] = "https://curaleaf.com" + feature["shopLink"]

        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in feature["openTimes"].items():
            for hours_range in day_hours:
                item["opening_hours"].add_range(day_name.title(), hours_range["startTime"], hours_range["endTime"], "%I:%M %p")

        apply_category(Categories.SHOP_CANNABIS, item)
        yield item
