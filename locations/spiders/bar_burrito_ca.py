from html import unescape

from phpserialize import unserialize

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarBurritoCASpider(WPStoreLocatorSpider):
    name = "bar_burrito_ca"
    item_attributes = {"brand": "BarBurrito", "brand_wikidata": "Q104844862", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["www.barburrito.ca"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["branch"] = unescape(item.pop("name"))
        del item["addr_full"]

        yield item

    def parse_opening_hours(self, location: dict, days: dict, **kwargs):
        # Reference: https://www.php.net/manual/en/function.unserialize.php
        php_serialized_string = location.get("hours", "").encode("utf-8")
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
