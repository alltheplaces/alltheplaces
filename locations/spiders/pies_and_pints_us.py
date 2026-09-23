import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Every restaurant is a block on the one store locations page. The address and
# phone share a single pipe separated line, and opening hours are written as
# "<days>: <times>" pairs.
#
# No coordinates are published anywhere on the site, and there are no per
# location pages, so features carry an address but no geometry.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class PiesAndPintsUSSpider(Spider):
    name = "pies_and_pints_us"
    item_attributes = {"brand": "Pies & Pints"}
    allowed_domains = ["piesandpints.net"]
    start_urls = ["https://piesandpints.net/store-locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[@class="location-filter"]//article'):
            item = Feature()
            item["branch"] = (location.xpath(".//h2/text()").get() or "").strip()
            item["ref"] = item["branch"]
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/text()').get()

            self.parse_address(item, location)

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "pizza"

            yield item

    @staticmethod
    def parse_address(item: Feature, location: Selector) -> None:
        """
        The address line is written either as
        "14550 Clay Terrace Blvd, Suite 100 | Carmel, IN  46032  | 317-688-7477"
        or with commas throughout, and always ends with the phone number.
        """
        line = " ".join(
            text.strip() for text in location.xpath('.//p[@class="address-phone"]//text()').getall() if text.strip()
        )
        line = re.sub(r"\s+", " ", line.replace("\xa0", " "))

        if not (address := re.match(r"^(.*)[|,]\s*([^|,]+),\s*([A-Z]{2})\s+(\d{5})", line)):
            item["addr_full"] = line
            return

        street, city, state, postcode = address.groups()
        item["street_address"] = street.strip(" |,")
        item["city"] = city.strip()
        item["state"] = state
        item["postcode"] = postcode

    @staticmethod
    def parse_opening_hours(location: Selector) -> OpeningHours | None:
        """Parses pairs such as "Sunday - Thursday: 11am - 9pm"."""
        oh = OpeningHours()

        text = " ".join(t.strip() for t in location.xpath(".//p[strong]//text()").getall() if t.strip())
        text = re.sub(r"\s+", " ", text).replace("\u2013", "-").replace("\u2014", "-")

        for days, open_time, close_time in re.findall(
            r"([A-Za-z][A-Za-z &-]*?)\s*:\s*(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)",
            text,
            re.I,
        ):
            day_names = []
            for token in re.split(r"&|\band\b", days):
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
                    PiesAndPintsUSSpider.normalise_time(open_time),
                    PiesAndPintsUSSpider.normalise_time(close_time),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").lower()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
