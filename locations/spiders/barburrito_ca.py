import json
from typing import Any, AsyncIterator, Iterable

from phpserialize import unserialize
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarburritoCASpider(WPStoreLocatorSpider):
    name = "barburrito_ca"
    item_attributes = {"brand": "BarBurrito", "brand_wikidata": "Q104844862"}
    allowed_domains = ["www.barburrito.ca"]
    days = DAYS_EN

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.barburrito.ca/locations/", callback=self.parse_ajax_url)

    def parse_ajax_url(self, response: Response, **kwargs: Any) -> Any:
        settings = json.loads(
            response.xpath('//script[contains(., "wpslSettings")]/text()').re_first(r"wpslSettings\s*=\s*(\{.+\});")
        )
        yield JsonRequest(url="{}&action=store_search&autoload=1".format(settings["ajaxurl"]), callback=self.parse)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("status") != "open":
            return
        item["branch"] = item.pop("name")
        apply_category(Categories.FAST_FOOD, item)
        yield item

    def parse_opening_hours(self, feature: dict, days: dict) -> OpeningHours:
        oh = OpeningHours()
        hours = unserialize(feature["hours"].encode(), decode_strings=True)
        if not any(hours.values()):
            return oh
        for day, ranges in hours.items():
            if not ranges:
                oh.set_closed(day)
                continue
            for time_range in ranges.values():
                open_time, close_time = time_range.split(",", 1)
                oh.add_range(day, open_time, close_time, "%I:%M %p" if "M" in time_range else "%H:%M")
        return oh
