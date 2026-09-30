import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page lists each bar as a card with its address, and passes the
# coordinates separately in a window.locations array keyed by the same page
# link. Phone and hours are only on each bar's own page.
#
# The first card on the page is the list's empty template.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class HotshotsUSSpider(Spider):
    name = "hotshots_us"
    item_attributes = {"brand": "Hotshots Sports Bar & Grill"}
    allowed_domains = ["hotshotsnet.com"]
    start_urls = ["https://hotshotsnet.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        coordinates = {}
        if locations := re.search(r"window\.locations\s*=\s*", response.text):
            for location in json.JSONDecoder().raw_decode(response.text[locations.end() :])[0]:
                coordinates[location["link"]] = location

        for card in response.xpath('//div[contains(@class, "loc-info")]'):
            page = card.xpath(".//h3/a/@href").get()
            if not page:
                continue

            item = Feature()
            item["ref"] = page.rstrip("/").rsplit("/", 1)[-1]
            # "Arnold, MO"
            item["branch"] = (card.xpath(".//h3/a/text()").get("") or "").rsplit(",", 1)[0].strip()
            item["street_address"] = card.xpath('.//span[@class="loc-street"]/text()').get("").strip()
            item["city"] = card.xpath('.//span[@class="loc-city"]/text()').get("").strip(" ,\t\n")
            item["state"] = card.xpath('.//span[@class="loc-state"]/text()').get("").strip()
            item["postcode"] = card.xpath('.//span[@class="loc-zip"]/text()').get("").strip()
            item["website"] = page

            if location := coordinates.get(page):
                item["lat"] = location.get("latitude")
                item["lon"] = location.get("longitude")

            apply_category(Categories.BAR, item)
            item["extras"]["cuisine"] = "american"

            yield response.follow(page, callback=self.parse_location, cb_kwargs={"item": item})

    def parse_location(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

        values = [
            re.sub(r"\s+", " ", value).strip()
            for value in response.xpath('//*[contains(@class, "hours")]//text()').getall()
            if value.strip()
        ]
        item["opening_hours"] = self.parse_opening_hours(values)

        yield item

    @staticmethod
    def parse_opening_hours(values: list[str]) -> OpeningHours | None:
        """The hours read "MON-SUN:" then "11:00 AM-1:30 AM", or "11AM-1:30AM"."""
        oh = OpeningHours()

        for label, hours in zip(values, values[1:]):
            if not (days := re.fullmatch(r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\s*:", label)):
                continue
            start, end = sanitise_day(days.group(1)), sanitise_day(days.group(2) or days.group(1))
            if not start or not end:
                continue
            if times := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", hours, re.I):
                oh.add_days_range(
                    day_range(start, end),
                    HotshotsUSSpider.normalise_time(times.group(1)),
                    HotshotsUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
