import re
from typing import AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# German Doner Kebab's own site (gdk.com) only operates a store locator for
# these five countries. Canada and the USA are served by entirely separate
# sites (gdkcanada.com, gdkusa.com) built on a different platform and are not
# covered by this spider.
COUNTRIES = {
    "gb": "GB",
    "ie": "IE",
    "ae": "AE",
    "se": "SE",
    "sa": "SA",
}

# Junk placeholder text that occasionally appears in the address widget in
# place of real address data (a source data quality issue, not a parsing bug).
IGNORED_ADDRESS_LINES = {"loading....", "no post code found"}


class GermanDonerKebabSpider(Spider):
    name = "german_doner_kebab"
    item_attributes = {
        "brand": "German Doner Kebab",
        "brand_wikidata": "Q112913418",
        "name": "German Doner Kebab",
    }
    allowed_domains = ["gdk.com"]
    # Roughly half of locations (mostly outside the UK) have no individual
    # page and thus no stable identifier provided by the source.
    no_refs = True

    async def start(self) -> AsyncIterator[Request]:
        for country_code in COUNTRIES:
            # "?cr=1" is required for the country-specific location list to
            # be rendered server-side; without it the page loads without any
            # locations present.
            yield Request(
                url=f"https://gdk.com/{country_code}/gdk-locations?cr=1",
                meta={"country_code": country_code},
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        country = COUNTRIES[response.meta["country_code"]]

        for location in response.css("div.location-item"):
            heading = location.css("h3.loc-heading::text").get()
            if not heading:
                continue

            item = Feature()
            item["branch"] = heading.strip()
            item["country"] = country

            if detail_url := location.css("a.loc-header::attr(href)").get():
                item["ref"] = item["website"] = response.urljoin(detail_url)

            address_lines = []
            for line in location.xpath('.//div[@class="loc-info"]/text()').getall():
                line = line.strip()
                if not line or line.lower() in IGNORED_ADDRESS_LINES or line.startswith("Open for"):
                    continue
                if line.startswith("Tel "):
                    item["phone"] = line.removeprefix("Tel ").strip()
                    continue
                address_lines.append(line)
            item["addr_full"] = merge_address_lines(address_lines)

            item["opening_hours"] = self.parse_hours(location)

            apply_category(Categories.FAST_FOOD, item)

            yield item

    @staticmethod
    def parse_hours(location) -> OpeningHours:
        oh = OpeningHours()
        for row in location.css(".loc-times-row"):
            day = row.css(".loc-weekday::text").get()
            clock = row.css(".loc-clocks::text").get()
            if not day or not clock or sanitise_day(day) is None:
                # A handful of locations have malformed weekday labels (e.g.
                # a one-off closure notice instead of a day name).
                continue
            clock = clock.strip()
            if clock.lower() == "closed":
                oh.set_closed(day.strip())
                continue
            if " - " not in clock:
                continue
            open_time, close_time = clock.split(" - ", 1)
            oh.add_range(
                day.strip(),
                GermanDonerKebabSpider.normalise_time(open_time),
                GermanDonerKebabSpider.normalise_time(close_time),
                time_format="%I:%M%p",
            )
        return oh

    @staticmethod
    def normalise_time(value: str) -> str:
        # e.g. "12am" -> "12:00am" so that it matches the "%I:%M%p" format
        # used for times which already include minutes, e.g. "10:30am".
        value = value.strip()
        if ":" not in value:
            value = re.sub(r"(am|pm)$", r":00\1", value, flags=re.IGNORECASE)
        return value
