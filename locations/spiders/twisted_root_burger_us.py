import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page is a Webflow collection, each card giving the address on
# two lines, the phone, and the hours as alternating day and time lines such as
# "Sunday - Thursday" then "11:00 am - 10:00 pm".
#
# No coordinates are published: the address links are Google short links.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})")


class TwistedRootBurgerUSSpider(Spider):
    name = "twisted_root_burger_us"
    item_attributes = {"brand": "Twisted Root Burger Co."}
    allowed_domains = ["twistedrootburgerco.com"]
    start_urls = ["https://twistedrootburgerco.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for card in response.xpath('//div[contains(@class, "item_cms-loc")]'):
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in card.xpath(".//p//text()").getall()
                if line.strip() and line.strip() != "Order it Now"
            ]
            if len(lines) < 2 or not (locality := ADDRESS.fullmatch(lines[1])):
                continue

            item = Feature()
            # "ABILENE"
            item["branch"] = (card.xpath(".//h1/text()").get("") or "").title().strip()
            item["street_address"] = lines[0]
            item["city"], item["state"], item["postcode"] = locality.groups()
            item["phone"] = card.xpath('.//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

            # The ordering link carries the chain's own slug for the restaurant.
            order_url = card.xpath('.//a[contains(@href, "order.incentivio.com")]/@href').get("")
            item["ref"] = order_url.rstrip("/").rsplit("/", 1)[-1] or re.sub(
                r"[^a-z0-9]+", "-", item["branch"].lower()
            ).strip("-")

            item["opening_hours"] = self.parse_opening_hours(lines[2:])

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "burger"

            yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The days and times alternate: "Sunday - Thursday", "11:00 am - 10:00 pm"."""
        oh = OpeningHours()

        for label, hours in zip(lines, lines[1:]):
            label = label.replace("\u2013", "-").replace("&", "-")
            if not (days := re.fullmatch(r"\s*([A-Za-z]{3,9})\s*-\s*([A-Za-z]{3,9})\s*", label)):
                continue
            start, end = sanitise_day(days.group(1)), sanitise_day(days.group(2))
            if not start or not end:
                continue

            times = hours.replace("\u2013", "-")
            if rule := re.fullmatch(
                r"\s*(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)\s*", times, re.I
            ):
                oh.add_days_range(
                    day_range(start, end),
                    TwistedRootBurgerUSSpider.normalise_time(rule.group(1)),
                    TwistedRootBurgerUSSpider.normalise_time(rule.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
