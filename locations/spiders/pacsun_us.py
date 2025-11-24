import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class PacsunUSSpider(JSONBlobSpider):
    name = "pacsun_us"
    item_attributes = {"brand": "PacSun", "brand_wikidata": "Q7121857"}
    requires_proxy = True
    start_urls = ["https://www.pacsun.com/on/demandware.store/Sites-pacsun-Site/default/Stores-FindStores?radius=30000"]
    locations_key = "stores"

    def pre_process_data(self, feature: dict) -> None:
        feature["street-address"] = merge_address_lines([feature["address1"], feature["address2"]])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = feature["seoURL"]
        item["opening_hours"] = OpeningHours()
        for start_day, end_day, start_time, end_time in re.findall(
            r"(\w+)(?: - (\w+))? (\d+:\d+ (?:AM|PM)) +- (\d+:\d+ (?:AM|PM))",
            feature["storeHours"],
        ):
            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day)

            if start_day and end_day:
                for day in day_range(start_day, end_day):
                    item["opening_hours"].add_range(day, start_time, end_time, time_format="%I:%M %p")
            elif start_day:
                item["opening_hours"].add_range(start_day, start_time, end_time, time_format="%I:%M %p")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
