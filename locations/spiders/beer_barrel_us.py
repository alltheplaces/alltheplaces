import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page links to a page per restaurant, each marking its address
# up with hCard classes and listing the hours a day at a time.
#
# The hours block also carries a "Kitchen until ..." line per rule, which is
# not the restaurant's own closing time.
#
# No coordinates are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BeerBarrelUSSpider(Spider):
    name = "beer_barrel_us"
    item_attributes = {"brand": "Beer Barrel Pizza & Grill"}
    allowed_domains = ["beerbarrel.com"]
    start_urls = ["https://beerbarrel.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(response.xpath('//a[@class and contains(@class, "location")]/@href').getall())):
            if path.startswith("/locations/"):
                yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["street_address"] = response.xpath('//*[contains(@class, "street-address")]/text()').get()
        item["city"] = response.xpath('//*[contains(@class, "locality")]/text()').get()
        item["state"] = response.xpath('//*[contains(@class, "region")]/text()').get()
        item["postcode"] = response.xpath('//*[contains(@class, "postal-code")]/text()').get()
        item["phone"] = response.xpath('//*[contains(@class, "tel")]//text()').re_first(
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        )
        if not item["street_address"]:
            return

        # "Lima Market Street" is the page heading plus the suburb below it.
        item["branch"] = " ".join(
            part.strip()
            for part in response.xpath('//h1//text() | //*[contains(@class, "suburb")]/text()').getall()
            if part.strip()
        )

        item["opening_hours"] = self.parse_opening_hours(
            response.xpath('//*[contains(@class, "hours")]//text()').getall()
        )

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    @staticmethod
    def parse_opening_hours(values: list[str]) -> OpeningHours | None:
        """The hours read "Monday-Thursday" then "11:00am-11:00pm", with a
        "Kitchen until ..." line after each rule."""
        oh = OpeningHours()

        values = [re.sub(r"\s+", " ", value).replace("\u2013", "-").replace("\u2014", "-").strip() for value in values]
        values = [value for value in values if value and not value.lower().startswith("kitchen")]

        for label, hours in zip(values, values[1:]):
            if not (days := re.fullmatch(r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?", label)):
                continue
            start, end = sanitise_day(days.group(1)), sanitise_day(days.group(2) or days.group(1))
            if not start or not end:
                continue
            if times := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I):
                oh.add_days_range(
                    day_range(start, end),
                    BeerBarrelUSSpider.normalise_time(times.group(1)),
                    BeerBarrelUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
