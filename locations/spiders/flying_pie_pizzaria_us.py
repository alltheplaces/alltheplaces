import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The site is a Nuxt app whose pages are server rendered, so the locations page
# links to a page per restaurant and each carries the address on one line, the
# phone, the hours and a Google Maps link holding the coordinates.
#
# The page heading is a marketing line rather than the branch, so the branch
# comes from the page title.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")


class FlyingPiePizzariaUSSpider(Spider):
    name = "flying_pie_pizzaria_us"
    item_attributes = {"brand": "Flying Pie Pizzaria"}
    allowed_domains = ["flyingpie.com"]
    start_urls = ["https://flyingpie.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(response.xpath("//a/@href").re(r"^/locations/[a-z]{2}/[a-z0-9-]+/[a-z0-9-]+$"))):
            yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        address = " ".join(response.xpath('//div[contains(@class, "location-address-info")]//text()').getall()).strip()
        if not (locality := ADDRESS.fullmatch(re.sub(r"\s+", " ", address))):
            return

        item = Feature()
        item["ref"] = response.url.replace("https://flyingpie.com/locations/", "")
        item["street_address"], item["city"], item["state"], item["postcode"] = locality.groups()
        item["website"] = response.url
        item["phone"] = response.xpath('//div[contains(@class, "location-phone-info")]//a/@href').re_first(r"tel:(.+)")

        # "Flying Pie Broadway - Boise, ID | Best Pizza Around! | Flying Pie"
        title = re.sub(r"\s+", " ", response.xpath("//title/text()").get("") or "")
        if branch := re.match(r"(?i)flying pie\s+(.+?)\s*[-\u2013]\s*[^,]+,\s*[A-Z]{2}", title):
            item["branch"] = branch.group(1).strip()

        # "https://maps.google.com/?q=43.5960438,-116.1931839"
        if coordinates := re.search(
            r"q=(-?\d+\.\d+),(-?\d+\.\d+)", response.xpath('//a[contains(@href, "maps.google")]/@href').get("")
        ):
            item["lat"], item["lon"] = coordinates.groups()

        item["opening_hours"] = self.parse_opening_hours(
            response.xpath('//*[contains(@class, "hours")]//text()').getall()
        )

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    @staticmethod
    def parse_opening_hours(values: list[str]) -> OpeningHours | None:
        """The days and times alternate: "Sunday - Thursday", "11:00 AM - 10:00 PM"."""
        oh = OpeningHours()

        values = [re.sub(r"\s+", " ", value).replace("\u2013", "-").strip() for value in values]
        values = [value for value in values if value]

        for label, hours in zip(values, values[1:]):
            if not (days := re.fullmatch(r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?", label)):
                continue
            start, end = sanitise_day(days.group(1)), sanitise_day(days.group(2) or days.group(1))
            if not start or not end:
                continue
            if times := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", hours, re.I):
                oh.add_days_range(
                    day_range(start, end),
                    FlyingPiePizzariaUSSpider.normalise_time(times.group(1)),
                    FlyingPiePizzariaUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
