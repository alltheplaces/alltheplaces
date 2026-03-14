from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiEEFILTLVSpider(JSONBlobSpider):
    name = "hyundai_ee_fi_lt_lv"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES | {"extras": Categories.SHOP_CAR.value}
    allowed_domains = ["locator.maplet.com"]
    start_urls = ["https://locator.maplet.com/api/public/v3/hyundai/places?type=place&layer=default"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["_id"]
        item["lat"] = feature["location"]["coordinates"][1]
        item["lon"] = feature["location"]["coordinates"][0]
        item["name"] = feature["name"]["fi"]
        item["street_address"] = feature["address"]["fi"]
        item["city"] = feature["city"]["fi"]
        item["postcode"] = feature["postcode"]
        item["country"] = feature["country"]["fi"]
        if item["country"] == "ET":
            # ISO 639 language code for Estonian is "ET"
            # ISO 3166-1 alpha-2 country code for Estonia is "EE"
            item["country"] = "EE"
        yield item
