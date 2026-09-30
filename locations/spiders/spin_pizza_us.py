import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page lists each restaurant as a card holding the address a line
# at a time, the phone and the hours, and passes the coordinates separately in
# a "locations" JavaScript array keyed by the same id.
#
# Closed restaurants are commented out of that array, and holiday notices are
# commented out inside the hours block.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class SpinPizzaUSSpider(Spider):
    name = "spin_pizza_us"
    item_attributes = {"brand": "SPIN! Neapolitan Pizza"}
    allowed_domains = ["www.spinpizza.com"]
    start_urls = ["https://www.spinpizza.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        coordinates = {}
        if locations := re.search(r"var locations\s*=\s*", response.text):
            for location in chompjs.parse_js_object(response.text[locations.end() :]):
                if len(location) == 4:
                    coordinates[str(location[1])] = (location[2], location[3])

        for card in response.xpath('//div[@class="location"]'):
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in card.xpath('.//div[@class="add"]/text()').getall()
                if line.strip()
            ]
            # "348 W Campbell Rd." / "Richardson, Texas" / "75080"
            if len(lines) < 3:
                continue

            item = Feature()
            item["ref"] = card.xpath("@id").get()
            # "SPIN! Richardson"
            item["branch"] = (card.xpath(".//strong/text()").get("") or "").removeprefix("SPIN!").strip()
            item["street_address"] = ", ".join(lines[:-2])
            item["city"], _, item["state"] = lines[-2].partition(",")
            item["postcode"] = lines[-1]
            item["phone"] = card.xpath('.//a[@class="loc-phone"]/text()').get()
            item["website"] = response.urljoin(card.xpath(".//a/@href").get())

            if location := coordinates.get(item["ref"]):
                item["lat"], item["lon"] = location

            item["opening_hours"] = self.parse_opening_hours(card.xpath('.//div[@class="hours"]/text()').getall())

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "pizza"

            yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The hours read "Sun-Sat: 11am-9pm"."""
        oh = OpeningHours()

        for line in lines:
            line = re.sub(r"\s+", " ", line).replace("\u2013", "-").strip()
            if not (
                rule := re.fullmatch(
                    r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\s*:\s*"
                    r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)",
                    line,
                    re.I,
                )
            ):
                continue

            start, end = sanitise_day(rule.group(1)), sanitise_day(rule.group(2) or rule.group(1))
            if not start or not end:
                continue

            oh.add_days_range(
                day_range(start, end),
                SpinPizzaUSSpider.normalise_time(rule.group(3)),
                SpinPizzaUSSpider.normalise_time(rule.group(4)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
