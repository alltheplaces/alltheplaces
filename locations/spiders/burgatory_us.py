import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Burgatory runs on Squarespace and its schema.org block is an empty template,
# so each restaurant page is read directly. Restaurants are the entries of the
# "Our Spots" folder in the site navigation.
#
# The address heading is written inconsistently: sometimes one line with
# commas, sometimes split across lines by a <br>, sometimes with no comma
# between street and city, and the stadium concession adds a venue name and a
# note.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BurgatoryUSSpider(Spider):
    name = "burgatory_us"
    item_attributes = {"brand": "Burgatory"}
    allowed_domains = ["burgatorybar.com"]
    start_urls = ["https://burgatorybar.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in set(
            response.xpath(
                '//div[@data-controller-folder="spots-1"]//a[@class="Mobile-overlay-folder-item"]/@href'
            ).getall()
        ):
            yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = response.xpath("//title/text()").re_first(r"Burgatory\s+([^|]+?)\s*\|") or item["ref"]
        item["website"] = response.url

        if not self.parse_address(item, response):
            return

        if phone := re.search(r"\b\d{3}[.\-]\d{3}[.\-]\d{4}\b", response.text):
            item["phone"] = phone.group(0)

        self.parse_position(item, response)

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "burger"

        yield item

    @staticmethod
    def parse_address(item: Feature, response: Response) -> bool:
        headings = response.xpath('//div[@class="sqs-html-content"]//h2')
        if not headings:
            return False

        lines = [text.strip() for text in headings[0].xpath(".//text()").getall() if text.strip()]

        for index, line in enumerate(lines):
            # "Pittsburgh, PA 15212", "2080 Mackenzie Way #600, Cranberry TWP, PA 16066"
            # or "700 Providence Blvd McCandless, PA 15237" with no comma at all.
            locality = re.search(r"(?:^|,\s*)([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5})", line) or re.search(
                r"\s([A-Za-z.'-]+),\s*([A-Z]{2})\s+(\d{5})", line
            )
            if not locality:
                continue

            item["city"], item["state"], item["postcode"] = [group.strip() for group in locality.groups()]
            street = line[: locality.start()].strip(" ,")
            # A street on an earlier line of the heading, e.g. after a <br>.
            item["street_address"] = street or " ".join(lines[:index][-1:])
            return bool(item["street_address"])

        return False

    @staticmethod
    def parse_position(item: Feature, response: Response) -> None:
        """
        Only the modern /maps/place/ links carry the restaurant's own
        coordinates. The older links on some pages hold a default map centre or,
        on the stadium concession page, an unrelated venue, so they are ignored.
        """
        for link in response.xpath('//a[contains(@href, "google.com/maps/place/")]/@href').getall():
            if coordinates := re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", unquote(link)):
                item["lat"], item["lon"] = coordinates.groups()
                return

    @staticmethod
    def parse_opening_hours(response: Selector) -> OpeningHours | None:
        """Parses lines such as "Sunday - Thursday 11 AM to 9 PM"."""
        oh = OpeningHours()

        for line in response.xpath('//div[@class="sqs-html-content"]//p//text()').getall():
            line = line.replace("\u2013", "-").replace("\u2014", "-").strip()
            # Happy hour is written in the same shape as the opening hours, and
            # is the only one that advertises prices.
            if "happy hour" in line.lower() or "$" in line:
                continue
            if not (
                times := re.search(
                    r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", line, re.I
                )
            ):
                continue

            day_names = []
            for token in re.split(r"&|\band\b", line[: times.start()].strip(" :")):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        day_names.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    day_names.append(day)

            if day_names:
                oh.add_days_range(
                    day_names,
                    BurgatoryUSSpider.normalise_time(times.group(1)),
                    BurgatoryUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").lower()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
