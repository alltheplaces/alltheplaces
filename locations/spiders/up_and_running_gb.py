from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class UpAndRunningGBSpider(StockistSpider):
    name = "up_and_running_gb"
    item_attributes = {"brand_wikidata": "Q42847650", "brand": "Up & Running", "extras": Categories.SHOP_SPORTS.value}
    key = "u7820"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Request]:
        for custom_field in feature["custom_fields"]:
            if custom_field["id"] == 1819:
                yield Request(url=custom_field["value"], meta={"item": item}, callback=self.parse_opening_hours)
                return

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        hours_text = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@class="map-section-content"]//p/text()').getall()))
        )
        hours_text = hours_text.replace(":0am", ":00am")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
