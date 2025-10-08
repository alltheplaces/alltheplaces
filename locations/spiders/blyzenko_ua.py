from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BlyzenkoUASpider(JSONBlobSpider):
    name = "blyzenko_ua"
    item_attributes = {"brand": "Близенько", "brand_wikidata": "Q117670418"}
    allowed_domains = ["blyzenko.ua"]
    start_urls = [
        "https://blyzenko.ua/wp-json/wp/v2/shops-list",
    ]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["acf_fields"].pop("shop_map"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["acf_fields"]["shop_id"]
        item["street_address"] = feature["acf_fields"]["shop_adress"]
        item["phone"] = feature["acf_fields"]["shop_tel"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(
            DAYS, feature["acf_fields"]["shop_start"], feature["acf_fields"]["shop_time_end"]
        )
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
