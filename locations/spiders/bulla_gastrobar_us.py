import json
import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAY = r"MON|TUES?|WED|THU(?:RS?)?|FRI|SAT|SUN"
TIME = r"\d{1,2}(?::\d{2})?\s*[AP]M"
# One run-on string holds a location's whole week, with the day labels sometimes
# followed by a colon and sometimes not: "MON-THUR: 11:30 AM - 10 PM FRI 11:30 AM..."
HOURS = re.compile(
    rf"(?P<days>(?:{DAY})(?:\s*[-–]\s*(?:{DAY}))?)\s*:?\s*"
    rf"(?:(?P<closed>CLOSED)|(?P<opens>{TIME})\s*[-–]\s*(?P<closes>{TIME}))",
    re.IGNORECASE,
)
LOCALITY = re.compile(r"^(?P<city>[^,]+),\s*(?P<state>[A-Za-z ]+?)\s+(?P<postcode>\d{5})$")
STATES = {"florida": "FL", "texas": "TX"}


class BullaGastrobarUSSpider(Spider):
    name = "bulla_gastrobar_us"
    item_attributes = {"brand": "Bulla Gastrobar"}
    start_urls = ["https://bullagastrobar.com/locations/"]

    @staticmethod
    def blocks(response: Response) -> list[list[str]]:
        """Return the location sidebar's labelled blocks, whose lines <br> separates."""
        blocks = []
        for block in response.xpath(
            '//div[contains(@class, "location_sidebar")]//div[contains(@class, "location_text")]'
        ).getall():
            lines = [
                re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", line)).strip() for line in re.split(r"<br[^>]*>", block)
            ]
            if lines := [line for line in lines if line]:
                blocks.append(lines)
        return blocks

    @staticmethod
    def labelled(blocks: list[list[str]], label: str) -> list[str]:
        """Return the lines of the block following the one that is just `label`."""
        for index, block in enumerate(blocks):
            if block[0].rstrip(":").casefold() == label.casefold() and index + 1 < len(blocks):
                return blocks[index + 1]
        return []

    def hours(self, text: str) -> OpeningHours:
        oh = OpeningHours()
        for match in HOURS.finditer(text):
            labels = re.split(r"\s*[-–]\s*", match["days"])
            if len(labels) == 2 and (start := sanitise_day(labels[0])) and (end := sanitise_day(labels[1])):
                days = day_range(start, end)
            else:
                days = [day] if (day := sanitise_day(labels[0])) else []
            if not match["closed"]:
                opens, closes = (self.normalise(match["opens"]), self.normalise(match["closes"]))
                if closes == "00:00":
                    # These kitchens close at midnight rather than opening for a minute.
                    closes = "24:00"
            for day in days:
                if match["closed"]:
                    oh.set_closed(day)
                else:
                    oh.add_range(day, opens, closes)
        return oh

    @staticmethod
    def normalise(time: str) -> str:
        """Read a time written as "11:30 AM", "10 PM" or "12AM"."""
        time = re.sub(r"\s+", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for link in response.xpath('//a[contains(@href, "/locations/")][span]'):
            url = link.xpath("@href").get("").rstrip("/") + "/"
            branch = link.xpath("span/text()").get("").strip()
            if url.endswith("/locations/") or not branch:
                continue
            yield response.follow(url, callback=self.parse_location, cb_kwargs={"branch": branch})

    def parse_location(self, response: Response, branch: str) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = branch

        blocks = self.blocks(response)
        address = self.labelled(blocks, "Location")
        for line in address:
            if locality := LOCALITY.match(line):
                item["city"] = locality["city"]
                item["state"] = STATES.get(locality["state"].casefold(), locality["state"])
                item["postcode"] = locality["postcode"]
            elif re.match(r"^\d", line):
                item["street_address"] = line

        contact = self.labelled(blocks, "Contact Us")
        item["phone"] = next((line for line in contact if re.match(r"^[\d().\- ]{10,}$", line)), None)
        item["email"] = next((line for line in contact if "@" in line), None)

        if hours := self.labelled(blocks, "Hours"):
            item["opening_hours"] = self.hours(" ".join(hours))

        # The page's structured data is unreliable: three of the eight pages carry
        # another location's record outright, so its coordinates are only used when
        # the record names the page it sits on.
        for restaurant in self.restaurants(response):
            if restaurant.get("url", "").rstrip("/") == response.url.rstrip("/"):
                if geo := restaurant.get("geo"):
                    item["lat"], item["lon"] = geo.get("latitude"), geo.get("longitude")

        if any("CASHLESS" in line for block in blocks for line in block):
            apply_yes_no(PaymentMethods.CASH, item, False, apply_positive_only=False)
            apply_yes_no(PaymentMethods.CARDS, item, True, apply_positive_only=False)

        # Luna Lounge is the rooftop bar of the Tampa restaurant, sharing its address
        # and phone but keeping its own hours, so it is a bar rather than a second
        # restaurant at the same address.
        apply_category(Categories.BAR if "Luna Lounge" in branch else Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "spanish;tapas"
        yield item

    @staticmethod
    def restaurants(response: Response) -> Iterable[dict]:
        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(ld)
            except json.JSONDecodeError:
                continue
            for node in data.get("@graph", [data]) if isinstance(data, dict) else []:
                if isinstance(node, dict) and node.get("@type") == "Restaurant":
                    yield node
