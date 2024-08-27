from html import unescape
from typing import Iterable

from phpserialize import unserialize
from scrapy.http import Response

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarburritoCASpider(WPStoreLocatorSpider):
    name = "barburrito_ca"
    item_attributes = {"brand": "BarBurrito", "brand_wikidata": "Q104844862", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["www.barburrito.ca"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = unescape(item.pop("name"))
        item.pop("addr_full", None)
        yield item

    def parse_opening_hours(self, feature: dict, days: dict) -> OpeningHours:
        # Reference: https://www.php.net/manual/en/function.unserialize.php
        php_serialized_string = feature.get("hours", "").encode("utf-8")
        unserialized_object = unserialize(php_serialized_string)
        unserialized_dict = {
            k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in unserialized_object.items()
        }
        unserialized_dict = {k: list(map(bytes.decode, v.values())) for k, v in unserialized_dict.items()}
        hours_string = ""
        for day_name, hour_ranges in unserialized_dict.items():
            for hour_range in hour_ranges:
                hours_string = "{} {}: {} - {}".format(
                    hours_string, day_name, hour_range.split(",", 1)[0], hour_range.split(",", 1)[1]
                )
        oh = OpeningHours()
        oh.add_ranges_from_string(hours_string)
        return oh
