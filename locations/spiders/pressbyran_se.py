from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class PressbyranSESpider(JSONBlobSpider):
    name = "pressbyran_se"
    item_attributes = {"brand": "Pressbyrån", "brand_wikidata": "Q2489072"}
    allowed_domains = ["public-store-data-prod.storage.googleapis.com"]
    start_urls = ["https://public-store-data-prod.storage.googleapis.com/stores-pressbyran.json"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        item["street_address"] = merge_address_lines(feature["address"])
        item["branch"] = item.pop("name").removeprefix("Pressbyrån ")
        item["opening_hours"] = OpeningHours()
        for day_hours in feature["openhours"]["standard"]:
            item["opening_hours"].add_range(DAYS[day_hours["weekday"]], day_hours["hours"][0], day_hours["hours"][1])
        apply_category(Categories.SHOP_KIOSK, item)
        yield item
