import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiIESpider(JSONBlobSpider):
    name = "hyundai_ie"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.ie"]
    start_urls = ["https://www.hyundai.ie/dealer-locator/dealer-list.json"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["MapCoordinates"].split(", ", 1)
        item["name"] = feature["DealerName"]
        item["website"] = "https://www.hyundai.ie/dealer/?dealer=" + feature["Slug"]

        sales = item.deepcopy()
        apply_category(Categories.SHOP_CAR, sales)
        sales["ref"] = feature["Slug"] + "_Sales"
        sales["opening_hours"] = OpeningHours()
        sales["opening_hours"].add_ranges_from_string(re.sub(r"\s+", " ", feature["OpeningHours"]))
        yield sales

        service = item.deepcopy()
        apply_category(Categories.SHOP_CAR_REPAIR, service)
        service["ref"] = feature["Slug"] + "_Service"
        service["opening_hours"] = OpeningHours()
        service["opening_hours"].add_ranges_from_string(re.sub(r"\s+", " ", feature["OpeningHours"]))
        yield service
