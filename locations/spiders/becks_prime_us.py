import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature

# The locations page links to a page per restaurant, and each page's Next.js
# data holds the address, phone, hours, feature list and a Google Maps embed
# whose URL carries the coordinates.
#
# The hours are a sentence, "7 days a week 11am-10pm".
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BecksPrimeUSSpider(Spider):
    name = "becks_prime_us"
    item_attributes = {"brand": "Beck's Prime"}
    allowed_domains = ["becksprime.com"]
    start_urls = ["https://becksprime.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(re.findall(r'"(/locations/[a-z0-9-]+)"', response.text))):
            yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        page_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not page_data:
            return

        location = json.loads(page_data)["props"]["pageProps"].get("location") or {}
        if not location or not location.get("active"):
            return

        item = Feature()
        item["ref"] = location["id"]
        item["branch"] = location.get("name")
        item["street_address"] = (location.get("street") or "").replace("\xa0", " ")
        item["city"] = location.get("city")
        item["state"] = location.get("state")
        item["postcode"] = location.get("zip")
        item["phone"] = location.get("phone")
        item["website"] = response.url

        # "!3d29.739817!2d-95.423538" in the Google Maps embed URL.
        if coordinates := re.search(r"!3d(-?\d+\.\d+)", location.get("mapLink") or ""):
            item["lat"] = coordinates.group(1)
        if coordinates := re.search(r"!2d(-?\d+\.\d+)", location.get("mapLink") or ""):
            item["lon"] = coordinates.group(1)

        features = {feature.lower() for feature in location.get("features") or []}
        apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("driveThru"), False)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "outdoor dining" in features, False)
        apply_yes_no(Extras.DELIVERY, item, bool(location.get("doorDashLink") or location.get("uberEatsLink")), False)

        item["opening_hours"] = self.parse_opening_hours(location.get("hours") or "")

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "burger"

        yield item

    @staticmethod
    def parse_opening_hours(hours: str) -> OpeningHours | None:
        """The hours read "7 days a week 11am-10pm"."""
        hours = hours.replace("\u2013", "-").replace("\u2014", "-")
        if not (times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I)):
            return None
        if not re.search(r"(?i)7 days|every ?day|daily", hours[: times.start()]):
            return None

        oh = OpeningHours()
        oh.add_days_range(
            ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
            BecksPrimeUSSpider.normalise_time(times.group(1)),
            BecksPrimeUSSpider.normalise_time(times.group(2)),
            time_format="%I:%M%p",
        )
        return oh

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
