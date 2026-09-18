import base64
import json
import re
from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours, day_range
from locations.items import Feature

# Matches a day, or day range (e.g. "MON-SAT"), at the start of an opening hours
# line, tolerating either a hyphen or plain whitespace before the time range that
# follows it (the site is inconsistent about which separator it uses).
DAY_LINE_RE = re.compile(
    r"^(" + "|".join(sorted(DAYS_EN, key=len, reverse=True)) + r")"
    r"(?:\s*-\s*(" + "|".join(sorted(DAYS_EN, key=len, reverse=True)) + r"))?"
    r"[\s-]+(.*)$",
    re.IGNORECASE,
)


class SchoopsHamburgersUSSpider(scrapy.Spider):
    name = "schoops_hamburgers_us"
    item_attributes = {
        "brand": "Schoop's Hamburgers",
        "brand_wikidata": "Q7432758",
        "name": "Schoop's Hamburgers",
    }
    start_urls = ["https://www.schoophamburgers.com/locations"]
    state_names = {"IN": "indiana", "IL": "illinois"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # The location list, including coordinates, only exists as a base64-encoded
        # JSON blob in this Duda "geo location" widget's data-editor attribute; there
        # is no separate API endpoint or sitemap that is reliably kept up to date (the
        # site's sitemap still contains menu pages for several since-closed locations).
        blob = response.xpath('//div[@data-element-type="dm_geo_location"]/@data-editor').get()
        for location in json.loads(base64.b64decode(blob))["locations"]:
            street, city, state_zip, _country = [p.strip() for p in location["formattedAddress"].split(",")]
            state, postcode = state_zip.split(" ")

            item = Feature()
            item["ref"] = str(location["uniqueId"])
            item["branch"] = city
            item["street_address"] = street
            item["city"] = city
            item["state"] = state
            item["postcode"] = postcode
            item["country"] = "US"
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["phone"] = location["phone"]
            apply_category(Categories.FAST_FOOD, item)

            # Tinley Park is run by a separate franchisee with its own website and,
            # unlike every other location, has no menu/hours page on the main site.
            if city == "Tinley Park":
                yield item
                continue

            item["website"] = "https://www.schoophamburgers.com/{}-{}-menu".format(
                city.lower().replace(" ", "-"), self.state_names[state]
            )
            yield scrapy.Request(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Any]:
        # Each page has one or more "list" widgets sharing the same markup, and an
        # unused/empty one (e.g. a specials list) sometimes comes before the real
        # hours list, so take the first one that actually has content.
        lines = []
        for span in response.xpath('//span[@class="itemName"]'):
            if lines := span.xpath(".//text()").getall():
                break

        oh = OpeningHours()
        for line in lines:
            if not (m := DAY_LINE_RE.match(line.strip())):
                continue  # e.g. a footnote line, not a day's hours
            days = day_range(m.group(1), m.group(2) or m.group(1))
            hours_text = m.group(3)
            if "closed" in hours_text.lower():
                oh.set_closed(days)
                continue
            times = re.findall(r"(\d{1,2}(?::\d{2})?)\s*([apAP][mM])", hours_text)
            if len(times) >= 2:
                oh.add_days_range(days, self.to_24h(*times[0]), self.to_24h(*times[1]))
        item["opening_hours"] = oh
        yield item

    @staticmethod
    def to_24h(value: str, meridiem: str) -> str:
        hour, _, minute = value.partition(":")
        hour, minute = int(hour), int(minute or 0)
        if meridiem.lower() == "pm" and hour != 12:
            hour += 12
        elif meridiem.lower() == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
