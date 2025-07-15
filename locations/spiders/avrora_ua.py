from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AvroraUASpider(JSONBlobSpider):
    name = "avrora_ua"
    item_attributes = {"brand": "Аврора", "brand_wikidata": "Q117669095"}
    allowed_domains = ["avrora.ua"]
    start_urls = ["https://avrora.ua/index.php?dispatch=pwa.store_locations&is_ajax=1"]
    locations_key = "objects"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("state", None)
        item["street_address"] = feature["name"]
        item["website"] = "https://avrora.ua/index.php?dispatch=store_locator.view&store_location_id={}".format(
            feature["shopNumber"]
        )
        item["phone"] = feature.get("pickup_phone")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature.get("pickup_time", ""), days=DAYS_RU)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
