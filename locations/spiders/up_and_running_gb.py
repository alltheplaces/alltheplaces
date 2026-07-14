from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class UpAndRunningGBSpider(StockistSpider):
    name = "up_and_running_gb"
    item_attributes = {"brand_wikidata": "Q42847650", "brand": "Up & Running"}
    key = "u7820"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Request]:
        item["branch"] = item.pop("name").removeprefix("Up & Running").strip()
        item["website"] = None
        apply_category(Categories.SHOP_SPORTS, item)
        for custom_field in feature["custom_fields"]:
            if custom_field["id"] == 1819:
                yield Request(url=custom_field["value"], meta={"item": item}, callback=self.parse_opening_hours)
                return
        yield item

    def parse_opening_hours(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = response.meta["item"]
        hours_text = " ".join(
            filter(
                None,
                map(
                    str.strip,
                    response.xpath(
                        '//h2[contains(., "Opening times")]'
                        '/following-sibling::div[contains(@class, "image-with-text__text")]//text()'
                    ).getall(),
                ),
            )
        )
        hours_text = hours_text.replace(":0am", ":00am")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
