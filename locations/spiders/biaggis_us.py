import html
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours, day_range
from locations.items import Feature

# Matches a "City, ST 12345" (optionally ZIP+4) trailing address line.
CITY_STATE_ZIP_RE = re.compile(r"^(?P<city>.+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5}(?:-\d{4})?)$")


class BiaggisUSSpider(scrapy.Spider):
    name = "biaggis_us"
    item_attributes = {
        "brand": "Biaggi's Ristorante Italiano",
        "brand_wikidata": "Q113754664",
        "name": "Biaggi's Ristorante Italiano",
    }
    start_urls = ["https://biaggis.com/locations/?state_search="]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # A single "find a location" page lists every restaurant, including
        # lat/lon and address, as data-* attributes (used to build a Google
        # Map on the page rather than derived from geocoding a link), so
        # extracting them here is reliable. The detail page for each
        # location (visited below) is intermittently blocked by a bot
        # protection plugin (CleanTalk); when that happens we still yield
        # the item using just what was found on this listing page.
        for location in response.css("div.location-archive-wrap"):
            addr_div = location.css("div.address")
            if not addr_div:
                continue

            item = Feature()
            item["lat"] = addr_div.attrib.get("data-lat")
            item["lon"] = addr_div.attrib.get("data-lng")
            item["branch"] = html.unescape(addr_div.attrib.get("data-name", "")).strip()

            detail_url = location.css("a.title-link::attr(href)").get()
            if detail_url:
                detail_url = response.urljoin(detail_url)
                item["website"] = detail_url
                item["ref"] = detail_url.rstrip("/").rsplit("/", 1)[-1]

            self.parse_address(item, addr_div.attrib.get("data-address", ""))

            apply_category(Categories.RESTAURANT, item)

            if detail_url:
                yield scrapy.Request(
                    detail_url, callback=self.parse_detail, errback=self.errback_item, meta={"item": item}
                )
            else:
                yield item

    def parse_address(self, item: Feature, data_address: str):
        text = html.unescape(data_address)
        text = re.sub(r"</?p>", "", text)
        lines = [line.strip() for line in re.split(r"<br\s*/?>", text) if line.strip()]
        if not lines:
            return

        m = CITY_STATE_ZIP_RE.match(lines[-1])
        if m:
            item["city"] = m.group("city")
            item["state"] = m.group("state")
            item["postcode"] = m.group("postcode")
            street_lines = lines[:-1]
        else:
            # Unexpected format, fall back to storing everything as-is.
            street_lines = lines

        if street_lines:
            item["street_address"] = ", ".join(street_lines)

    def parse_detail(self, response: Response) -> Any:
        item = response.meta["item"]
        yield from self.finish_item(item, response)

    def errback_item(self, failure):
        # The location detail page can be intermittently blocked by the
        # site's bot protection. Still yield what was found on the listing
        # page rather than dropping the location entirely.
        item = failure.request.meta["item"]
        yield item

    def finish_item(self, item: Feature, response: Response) -> Any:
        phone = response.css("div.phone-number a::attr(href)").get()
        if phone:
            item["phone"] = phone.removeprefix("tel:").strip()

        oh = OpeningHours()
        for row in response.css(".opening-hours-row"):
            day_text = row.css(".day::text").get()
            open_time = row.css(".time-open::text").get()
            close_time = row.css(".time-close::text").get()
            if not (day_text and open_time and close_time):
                continue

            day_text = day_text.strip().rstrip(":").strip()
            close_time = re.sub(r"\s*Last Seating.*", "", close_time, flags=re.I).strip()

            if day_text.lower() == "daily":
                days = DAYS
            else:
                # Day ranges/lists appear as e.g. "Monday - Saturday",
                # "Sunday-Thursday" or "Friday & Saturday".
                normalised = re.sub(r"\s*(&|and)\s*", "-", day_text, flags=re.I)
                parts = [d.strip() for d in normalised.split("-") if d.strip()]
                if not parts:
                    continue
                try:
                    days = day_range(parts[0], parts[-1])
                except ValueError:
                    continue

            oh.add_days_range(days, open_time.strip(), close_time, time_format="%I:%M%p")

        if oh:
            item["opening_hours"] = oh

        yield item
