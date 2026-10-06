import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page lists each restaurant as a card holding the branch, the
# street, "city, state postcode", the phone and the hours.
#
# Coordinates come from the directions link, where the card has one; four cards
# have none and one has a typo in its URL scheme.
#
# Two restaurants publish separate winter and summer hours, so only the first
# block is read.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class CafeSaborUSSpider(Spider):
    name = "cafe_sabor_us"
    item_attributes = {"brand": "Cafe Sabor"}
    allowed_domains = ["www.cafesabor.com"]
    start_urls = ["https://www.cafesabor.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for card in response.xpath('//div[contains(@class, "el-item")]'):
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in card.xpath('.//div[@class="tm-overlay-meta"]//text()').getall()
                if line.strip()
            ]
            locality = next((index for index, line in enumerate(lines) if ADDRESS.fullmatch(line)), None)
            if locality is None or locality == 0:
                continue

            item = Feature()
            # "Logan, UT", "REXBURG, id"
            heading = re.sub(r"\s+", " ", card.xpath('.//h3[contains(@class, "el-title")]/text()').get("")).strip()
            item["branch"] = re.sub(r",\s*[A-Za-z]{2}$", "", heading).title()
            item["street_address"] = ", ".join(lines[:locality])
            item["city"], item["state"], item["postcode"] = ADDRESS.fullmatch(lines[locality]).groups()
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{item['branch']} {item['postcode']}".lower()).strip("-")

            if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
                item["phone"] = phone.group(0)

            # "http://maps.google.com/?daddr=41.731623,-111.850026", with one
            # card's scheme mistyped as "hhttps".
            if coordinates := re.search(
                r"daddr=(-?\d+\.\d+),(-?\d+\.\d+)", card.xpath('.//a[contains(@href, "maps.google")]/@href').get("")
            ):
                item["lat"], item["lon"] = coordinates.groups()

            item["opening_hours"] = self.parse_opening_hours(lines[locality:])

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "mexican"

            yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The days and times alternate: "MONDAY-WEDNESDAY:" then "11am-9:00pm"."""
        oh = OpeningHours()

        for label, hours in zip(lines, lines[1:]):
            # A second "SUMMER:" block follows the winter one at two
            # restaurants; the first block is the current one.
            if re.fullmatch(r"(?i)summer:?", label) and oh:
                break

            if not (days := re.fullmatch(r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\s*:", label)):
                continue
            start, end = sanitise_day(days.group(1)), sanitise_day(days.group(2) or days.group(1))
            if not start or not end:
                continue

            if "closed" in hours.lower():
                for day in day_range(start, end):
                    oh.set_closed(day)
                continue
            if times := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I):
                oh.add_days_range(
                    day_range(start, end),
                    CafeSaborUSSpider.normalise_time(times.group(1)),
                    CafeSaborUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
