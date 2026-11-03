import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class AbcAutoPartsUSSpider(Spider):
    name = "abc_auto_parts_us"
    item_attributes = {"brand": "ABC Auto Parts"}
    allowed_domains = ["abcauto.com"]
    start_urls = ["https://abcauto.com/StoreLocator"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[contains(@class, "store-card")][@data-lat]'):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/@href').get("")

            # "ABC Auto Parts, 3667 Estes Pkwy, Longview, TX, 75603"
            query = unquote(
                location.xpath('.//a[contains(@href, "google.com/maps")]/@href').get("").split("query=")[-1]
            ).replace("+", " ")
            parts = [part.strip() for part in query.split(",")]
            if len(parts) < 5:
                continue
            item["street_address"], item["city"], item["state"], item["postcode"] = parts[-4:]

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.SHOP_CAR_PARTS, item)

            yield item

    @staticmethod
    def parse_opening_hours(location: Selector) -> OpeningHours | None:
        """The hours list alternates a day name and its "7:30AM - 7:00PM" times."""
        oh = OpeningHours()

        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in location.xpath('.//div[contains(@class, "store-hours")]//text()').getall()
            if line.strip()
        ]

        for day, times in zip(lines, lines[1:]):
            if not (day := DAYS_EN.get(day.title())):
                continue
            if rule := re.fullmatch(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", times, re.I):
                oh.add_range(
                    day, rule.group(1).replace(" ", "").upper(), rule.group(2).replace(" ", "").upper(), "%I:%M%p"
                )

        return oh if oh.as_opening_hours() else None
