import re
import time

from scrapy.spiders import SitemapSpider

from locations.categories import Drink, Extras, Sells, apply_yes_no
from locations.hours import CLOSED_EN, DAYS, OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider

# Each store page states the number the chain knows it by in the analytics call
# it makes as it loads.
LOCATION_NUMBER = re.compile(r"dimensionLocationNumber['\"]?\s*:\s*['\"](\d+)['\"]")
# What a store offers is published as an escaped JSON string in a script.
AMENITIES = re.compile(r"amenitiesString\s*=\s*\"(.*?)\"\s*;", re.S)
AMENITY = re.compile(r"&quot;(\w+)&quot;:&quot;(\w+)&quot;")
# A store that has not opened yet puts these words where its times belong.
NOT_OPEN_YET = "COMING SOON"
# The attributes a store states about itself, and the tag each one belongs in.
OFFERINGS = (
    ("has_drive_through", Extras.DRIVE_THROUGH),
    ("has_seating", Extras.INDOOR_SEATING),
    ("serves_breakfast", Extras.BREAKFAST),
    ("serves_lunch", Extras.LUNCH),
    ("serves_alcohol", Sells.ALCOHOL),
    ("serves_beer", Drink.BEER),
)


class JackInTheBoxSpider(SitemapSpider, StructuredDataSpider):
    """Every store states itself as linked data on a page of its own.

    Asked for a page a second the site answers about a hundred of them and then
    refuses this caller everything, the sitemap and robots.txt included, for a
    good while afterwards. That is what held earlier runs to a twentieth of the
    chain, so the requests are spread across the proxy pool, no one address
    carrying enough of them to be counted out.

    The chain writes the hours of a store that trades right through a day as a
    single time at both ends of that day, four in the morning being the hour its
    own trading day turns over. Read literally that is a range of no length,
    which the library discards, so two thirds of the chain arrived with no hours
    at all. Such a day is recorded here as open throughout instead.
    """

    name = "jack_in_the_box"
    item_attributes = {"brand": "Jack in the Box", "brand_wikidata": "Q1538507"}
    sitemap_urls = ["https://locations.jackinthebox.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    json_parser = "chompjs"
    time_format = "%I:%M %p"
    requires_proxy = True
    # Every page's footer links the chain's own social accounts, which say
    # nothing about the store whose page it is.
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data, **kwargs):
        # Times are written with the stops left in, as "04:00 A.M.", which the
        # library cannot read.
        for rule in ld_data.get("openingHoursSpecification", []):
            rule["opens"] = (rule.get("opens") or "").replace(".", "")
            rule["closes"] = (rule.get("closes") or "").replace(".", "")

    def post_process_item(self, item, response, ld_data, **kwargs):
        specification = ld_data.get("openingHoursSpecification") or []

        if self.not_open_yet(specification):
            self.logger.info(f"{response.url} has not opened yet, so it is not published")
            return

        item["opening_hours"] = self.parse_hours(specification)

        # The name is the chain's own, which the brand already carries.
        item.pop("name", None)
        if number := LOCATION_NUMBER.search(response.text):
            item["ref"] = number.group(1)
        item["website"] = response.url

        self.apply_offerings(item, response)

        yield item

    @staticmethod
    def not_open_yet(specification: list) -> bool:
        return any(
            NOT_OPEN_YET in str(rule.get("opens") or "").upper()
            or NOT_OPEN_YET in str(rule.get("closes") or "").upper()
            for rule in specification
        )

    def parse_hours(self, specification: list) -> OpeningHours | str:
        stated = {}
        for rule in specification:
            day = sanitise_day((rule.get("dayOfWeek") or "").rsplit("/", 1)[-1])
            opens = str(rule.get("opens") or "").replace(".", "").strip()
            closes = str(rule.get("closes") or "").replace(".", "").strip()
            if day and opens and closes:
                stated[day] = (opens, closes)

        closed = {day for day, (opens, closes) in stated.items() if opens.lower() in CLOSED_EN}
        # A day given as one time is a day of trading right the way through it.
        round_the_clock = {day for day, (opens, closes) in stated.items() if opens == closes and day not in closed}
        if len(round_the_clock) == len(DAYS):
            return "24/7"

        oh = OpeningHours()
        for day, (opens, closes) in stated.items():
            if day in closed:
                oh.set_closed(day)
                continue
            if day in round_the_clock:
                oh.add_range(day, "00:00", "24:00", time_format="%H:%M")
                continue
            try:
                opens, closes = self.as_24_hour(opens), self.as_24_hour(closes)
            except ValueError:
                self.logger.warning(f"Unparsed hours {opens!r} to {closes!r} on {day}")
                continue
            # Where a day closes in the small hours of a day that then trades
            # right through, those hours are already covered by it, so this
            # range is left to run to midnight rather than stated twice over.
            if closes <= opens and DAYS[(DAYS.index(day) + 1) % len(DAYS)] in round_the_clock:
                closes = "24:00"
            oh.add_range(day, opens, closes, time_format="%H:%M")
        return oh

    @staticmethod
    def as_24_hour(value: str) -> str:
        return time.strftime("%H:%M", time.strptime(value, "%I:%M %p"))

    def apply_offerings(self, item, response) -> None:
        """Record what a store offers, each of which it states as true or false."""
        if not (found := AMENITIES.search(response.text)):
            return
        offerings = {key: value.lower() == "true" for key, value in AMENITY.findall(found.group(1))}
        for key, tag in OFFERINGS:
            if key in offerings:
                apply_yes_no(tag, item, offerings[key], apply_positive_only=False)
