import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider

LOCATOR = "https://www.thepalm.com/store-locator/"
# The hours are published nowhere but the description the site writes for
# search engines, which gives them as a sentence. Everything from the first of
# these onward is something other than the hours the restaurant keeps.
NOT_TRADING = re.compile(r"Happy Hour|Brunch Available|Holiday Hours", re.IGNORECASE)
# "Monday to Thursday from 11:30 AM to 9:00 PM", and the two other ways the
# same sentence is written: "SUN: 4:00 PM - 9:00 PM" at one restaurant, and
# "Main Menu Served Daily from 10:30 AM to 10:00 PM" at the one in an airport.
RULE = re.compile(
    r"(?P<days>[A-Za-z]+(?:\s*(?:to|-)\s*[A-Za-z]+)?)\s*:?\s*(?:from\s*)?"
    r"(?P<opens>\d{1,2}:\d{2}\s*[AP]M)\s*(?:to|-)\s*(?P<closes>\d{1,2}:\d{2}\s*[AP]M)",
    re.IGNORECASE,
)
DAILY = re.compile(r"daily|every\s*day", re.IGNORECASE)
ALL_WEEK = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class ThePalmSpider(StructuredDataSpider):
    """The locator states every restaurant inside one piece of linked data, and
    each of them keeps a page of its own which states it over again as linked
    data in its own right - its address, its telephone number and the page it
    takes bookings through.

    Those pages are read rather than the locator alone, for two things the
    locator does not give: the photograph of the restaurant itself, and the
    hours it keeps.

    No coordinates are published anywhere. The field that would carry a map
    holds the restaurant's own page instead, and nothing on that page states a
    position either.
    """

    name = "the_palm"
    # Neither the chain nor any of its restaurants has a Wikidata item.
    item_attributes = {"brand": "The Palm"}
    allowed_domains = ["www.thepalm.com"]
    start_urls = [LOCATOR]
    wanted_types = ["FoodEstablishment"]
    # The accounts on X and on Facebook are the chain's own, one of each
    # between the seventeen restaurants, and the picture the linked data
    # carries is the chain's as well - two pictures between the seventeen - so
    # the picture the page offers a reader is taken instead, that one being the
    # restaurant's own.
    search_for_twitter = False
    search_for_facebook = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for stated in LinkedDataParser.iter_linked_data(response):
            for restaurant in stated.get("subOrganization") or []:
                if page := restaurant.get("url"):
                    yield response.follow(page, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        # The linked data names the restaurant after its own page, with a
        # fragment behind it that the page address already carries.
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # Each restaurant is named for the place it stands in.
        item["branch"] = item.pop("name", None)

        # No country is stated for any of them. The one restaurant outside the
        # United States gives its region as "MX-DIF", naming its country in
        # front of it, and the rest give a bare state code.
        if region := item.get("state"):
            if "-" in region:
                item["country"], item["state"] = region.split("-", 1)
            else:
                item["country"] = "US"

        item["image"] = response.xpath('//meta[@property="og:image"]/@content').get()
        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house;italian"
        yield item

    def parse_hours(self, response: Response) -> OpeningHours | None:
        stated = re.sub(r"[–—]", "-", response.xpath('//meta[@name="description"]/@content').get() or "")
        keeping = OpeningHours()
        for rule in RULE.finditer(NOT_TRADING.split(stated)[0]):
            if not (days := self.parse_days(rule["days"])):
                continue
            opens, closes = (re.sub(r"\s+", "", rule[part]).upper() for part in ("opens", "closes"))
            for day in days:
                keeping.add_range(day, opens, closes, time_format="%I:%M%p")
        return self.merge(keeping) if keeping.as_opening_hours() else None

    @staticmethod
    def parse_days(stated: str) -> list[str]:
        if DAILY.fullmatch(stated := stated.strip()):
            return list(ALL_WEEK)
        # One restaurant abbreviates the days, as "MON - THU", so a name that
        # is not known is tried again by its first three letters.
        named = [part.strip() for part in re.split(r"\s*(?:to|-)\s*", stated) if part.strip()]
        days = [sanitise_day(part) or sanitise_day(part[:3]) for part in named]
        if not all(days):
            return []
        return day_range(days[0], days[-1]) if len(days) > 1 else [days[0]]

    @staticmethod
    def merge(hours: OpeningHours) -> OpeningHours:
        """Draw the services of a day together into the hours it keeps.

        The restaurant in the airport states a breakfast and then a main menu
        taking over where it leaves off, which is one unbroken day rather than
        two sittings.
        """
        merged = OpeningHours()
        for day, ranges in hours.day_hours.items():
            spans: list[list[int]] = []
            for start, end in sorted(
                (start.tm_hour * 60 + start.tm_min, end.tm_hour * 60 + end.tm_min) for start, end in ranges
            ):
                if spans and start <= spans[-1][1]:
                    spans[-1][1] = max(spans[-1][1], end)
                else:
                    spans.append([start, end])
            for start, end in spans:
                merged.add_range(day, f"{start // 60:02}:{start % 60:02}", f"{end // 60:02}:{end % 60:02}")
        return merged
