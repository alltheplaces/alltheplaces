import html
import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The Wix locations page links to a page per restaurant through its "view
# details" buttons. Each page holds the branch, address and phone in rich text
# blocks, split by line breaks rather than by elements, and the coordinates in
# the Google Maps link beside the address.
#
# The hours block is followed by a happy hour block, which is not the
# restaurant's own opening hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\d{3}[-.]\d{3}[-.]\d{4}")


class GarciasMexicanRestaurantUSSpider(Spider):
    name = "garcias_mexican_restaurant_us"
    item_attributes = {"brand": "Garcia's Mexican Restaurant"}
    allowed_domains = ["www.garciasmexicanrestaurants.net"]
    start_urls = ["https://www.garciasmexicanrestaurants.net/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in sorted(set(response.xpath('//a[@aria-label="VIEW DETAILS"]/@href').getall())):
            yield response.follow(url, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        blocks = [self.lines(block.get()) for block in response.xpath('//div[@data-testid="richTextElement"]')]
        blocks = [block for block in blocks if block]
        # Most pages give the branch, address and phone as separate blocks; one
        # combines them, so the lines are read in order rather than per block.
        lines = [line for block in blocks for line in block]

        locality = next((index for index, line in enumerate(lines) if ADDRESS.fullmatch(line)), None)
        if locality is None or locality == 0:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["street_address"] = lines[locality - 1]
        item["city"], item["state"], item["postcode"] = ADDRESS.fullmatch(lines[locality]).groups()
        item["branch"] = lines[locality - 2] if locality >= 2 else None
        item["website"] = response.url
        if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
            item["phone"] = phone.group(0)

        # "...!3d33.6384449!4d-112.1816305" in the Google Maps place link.
        maps = response.xpath('//a[contains(@href, "maps/place")]/@href').get("")
        if coordinates := re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", maps):
            item["lat"], item["lon"] = coordinates.groups()

        item["opening_hours"] = self.parse_opening_hours(blocks)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "mexican"

        yield item

    @staticmethod
    def lines(markup: str) -> list[str]:
        """The block's lines are separated by <br>, not by elements."""
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))).strip() for part in parts]
        return [part for part in parts if part]

    @staticmethod
    def parse_opening_hours(blocks: list[list[str]]) -> OpeningHours | None:
        """The hours read "Sun - Thurs 11am - 9pm", with happy hours in their own block."""
        oh = OpeningHours()

        for block in blocks:
            joined = " ".join(block).lower()
            if "happy hour" in joined or "hours" not in joined:
                continue

            for line in block:
                line = line.replace("\u2013", "-").replace("&", "-")
                if not (
                    times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)
                ):
                    continue

                days = []
                for part in re.split(r",|\band\b", line[: times.start()]):
                    tokens = [day for token in part.split("-") if (day := sanitise_day(token.strip(" :-")))]
                    if len(tokens) == 2:
                        days.extend(day_range(tokens[0], tokens[1]))
                    else:
                        days.extend(tokens)
                if not days:
                    continue

                opens = GarciasMexicanRestaurantUSSpider.normalise_time(times.group(1))
                closes = GarciasMexicanRestaurantUSSpider.normalise_time(times.group(2))
                # One restaurant's Sunday line reads "11pm - 7pm", which would
                # wrap around most of the following day.
                if GarciasMexicanRestaurantUSSpider.span_hours(opens, closes) > 18:
                    continue

                oh.add_days_range(days, opens, closes, time_format="%I:%M%p")

        return oh if oh else None

    @staticmethod
    def span_hours(opens: str, closes: str) -> float:
        """How long the range runs, counting a closing time before the opening as the next day."""
        start = datetime.strptime(opens, "%I:%M%p")
        end = datetime.strptime(closes, "%I:%M%p")
        return ((end - start).total_seconds() / 3600) % 24

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
