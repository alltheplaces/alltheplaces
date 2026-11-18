import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature

# The all-locations page labels what each entry actually is. Most of the chain's
# entries are a pie counter hosted inside a Famous Dave's or Tahoe Joe's rather than
# a Baker's Square, and two restaurants have been converted to Village Inn, so
# neither kind is a Baker's Square restaurant at that address.
NOT_A_RESTAURANT = re.compile(r"(?i)pie only|now village inn")
HOURS = re.compile(
    r"^(?P<day>[A-Za-z]+):\s*(?:(?P<closed>closed)|(?P<opens>[\d: apm]+?)\s*[-–]\s*(?P<closes>[\d: apm]+))$",
    re.IGNORECASE,
)
COORDINATES = re.compile(r"lat:\s*(?P<lat>-?\d+\.\d+),\s*lng:\s*(?P<lon>-?\d+\.\d+)")


class BakersSquareUSSpider(Spider):
    name = "bakers_square_us"
    item_attributes = {"brand": "Bakers Square", "brand_wikidata": "Q4849272"}
    start_urls = ["https://www.bakerssquare.com/locations/"]

    @staticmethod
    def normalise(time: str) -> str:
        """Read a time written as "8 am", "10:30 pm" or "9 PM"."""
        time = re.sub(r"\s+", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def hours(self, lines: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for line in lines:
            if not (match := HOURS.match(line)) or not (day := sanitise_day(match["day"])):
                continue
            if match["closed"]:
                oh.set_closed(day)
            else:
                oh.add_range(day, self.normalise(match["opens"]), self.normalise(match["closes"]))
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for entry in response.xpath('//div[contains(@class, "locations-list")]//li[a/@href]'):
            label = entry.xpath("normalize-space(a)").get("")
            if NOT_A_RESTAURANT.search(label):
                continue
            yield response.follow(entry.xpath("a/@href").get(), callback=self.parse_location)

    def parse_location(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        # The heading opens with a "Favorite" button, so only its own text is the name.
        item["branch"] = response.xpath('normalize-space(//div[contains(@class, "location-details")]//h1/text())').get()

        for field, prop in (
            ("street_address", "streetAddress"),
            ("city", "addressLocality"),
            ("state", "addressRegion"),
            ("postcode", "postalCode"),
        ):
            item[field] = response.xpath(f'normalize-space(//*[@itemprop="{prop}"])').get() or None
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in response.xpath('//ul[@class="hours"]/li').xpath("string()").getall()
        ]
        item["opening_hours"] = self.hours(lines)

        # The only coordinates on the page centre its map, and each page carries its
        # own rather than a shared default.
        if pin := COORDINATES.search(response.text):
            item["lat"], item["lon"] = pin["lat"], pin["lon"]

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "american;pie"
        yield item
