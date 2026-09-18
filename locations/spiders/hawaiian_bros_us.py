import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page is a Webflow collection. Every restaurant is a card with
# its coordinates and city in data attributes, the address split across inline
# divs, and the hours as free text.
#
# Restaurants that have not opened yet, and temporarily closed ones, are marked
# by a tag that Webflow leaves in the markup and hides with the
# w-condition-invisible class, so the visible tag is what identifies them.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class HawaiianBrosUSSpider(Spider):
    name = "hawaiian_bros_us"
    item_attributes = {"brand": "Hawaiian Bros Island Grill"}
    allowed_domains = ["hawaiianbros.com"]
    start_urls = ["https://hawaiianbros.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[@id="source-list"]//div[contains(@class, "location-list_card")]'):
            if location.xpath(
                './/div[contains(@class, "map-list_tag") and not(contains(@class, "w-condition-invisible"))]/text()'
            ).get():
                continue

            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["branch"] = location.xpath(".//h3/text()").get()
            # A handful of open restaurants have the coordinate attributes
            # present but empty.
            item["lat"] = location.xpath("@data-lat").get() or None
            item["lon"] = location.xpath("@data-lng").get() or None
            item["city"] = location.xpath("@data-city").get()
            item["postcode"] = location.xpath("@data-zip").get()
            item["state"] = location.xpath("@data-state").get()
            item["website"] = response.urljoin(location.xpath('.//a[contains(@href, "/locations/")]/@href').get(""))
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/text()').get()

            # The address is split across inline divs, the first of which is the
            # street and the rest of which repeat the city, state and postcode.
            if street := location.xpath('.//div[contains(@class, "map-list_address")]/div[1]/text()').get():
                item["street_address"] = street.strip()

            self.parse_amenities(item, location)

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "hawaiian"

            yield item

    @staticmethod
    def parse_amenities(item: Feature, location: Selector) -> None:
        for option in location.xpath('.//div[contains(@class, "map-list_store-option")]'):
            title = (
                option.xpath('.//div[contains(@class, "map-list_store-option-title")]/text()').get() or ""
            ).strip()
            # Webflow hides the answer that does not apply.
            answer = option.xpath(
                './/div[contains(@class, "map-list_store-option-data")]'
                '[not(contains(@class, "w-condition-invisible"))]//div[last()]/text()'
            ).get()
            if title == "Drive-Thru":
                apply_yes_no(Extras.DRIVE_THROUGH, item, answer == "Yes", False)
            elif title == "Dine-In":
                apply_yes_no(Extras.INDOOR_SEATING, item, answer == "Yes", False)

    @staticmethod
    def parse_opening_hours(location: Selector) -> OpeningHours | None:
        """Parses free text such as "Monday-Sunday:" / "10AM - 3AM"."""
        oh = OpeningHours()

        text = " ".join(
            part.strip()
            for part in location.xpath('.//div[contains(@class, "w-richtext")]//text()').getall()
            if part.strip()
        )
        text = text.replace("\u2013", "-").replace("\u2014", "-")

        for days, open_time, close_time in re.findall(
            r"([A-Za-z][A-Za-z\- ]*?)\s*:\s*(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)",
            text,
            re.I,
        ):
            day_names = []
            for token in re.split(r"&|,|\band\b", days):
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
                    HawaiianBrosUSSpider.normalise_time(open_time),
                    HawaiianBrosUSSpider.normalise_time(close_time),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
