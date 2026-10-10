import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Canadian province/territory codes used by the dealer locator, to
# distinguish Canadian dealers from US dealers (both use two letter
# codes in the "State" field).
CANADIAN_PROVINCES = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}

TIME_RE = re.compile(r"^(\d{1,2})[.:](\d{2})\s*([ap]\.?m\.?)?$", re.IGNORECASE)

# A generic corporate intake address shared by a large fraction of Canadian
# dealers, rather than a branch-specific contact.
SHARED_EMAILS = {"info@culliganwater.ca"}


class CulliganSpider(Spider):
    name = "culligan"
    item_attributes = {"brand": "Culligan", "brand_wikidata": "Q5193025", "name": "Culligan"}
    start_urls = ["https://www.culligan.com/locations"]
    # Each dealer's own hours are keyed by day in the API response.
    hour_fields = {
        "Mo": "OfficeHourMon",
        "Tu": "OfficeHourTue",
        "We": "OfficeHourWed",
        "Th": "OfficeHourThu",
        "Fr": "OfficeHourFri",
        "Sa": "OfficeHourSat",
        "Su": "OfficeHourSun",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        api_response = next_data["props"]["pageProps"]["apiResponse"]
        dealers = api_response["usDealers"] + api_response["canadaDealers"]

        seen_slugs = set()
        for dealer in dealers:
            slug = dealer["slug"]
            # A handful of test/placeholder entries and mislabeled duplicates
            # exist in this directory; the individual dealer page 404s/redirects
            # for these so they are simply skipped rather than crawled.
            if slug in seen_slugs or "test" in slug.lower():
                continue
            seen_slugs.add(slug)

            state = dealer["state"].lower()
            slug_stem = slug.removesuffix(f"-{state}")
            yield response.follow(f"/locations/{state}/{slug_stem}", callback=self.parse_dealer)

    def parse_dealer(self, response: Response, **kwargs: Any) -> Any:
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        api_response = next_data["props"]["pageProps"]["apiResponse"]
        dealers = api_response.get("dealerLocatorResponse", {}).get("aryDealer", {}).get("Dealer") or []
        if not dealers:
            return
        dealer = dealers[0]

        item = Feature()
        item["ref"] = dealer["DealerNumber"]
        item["name"] = dealer["Title"].strip()
        item["street_address"] = ", ".join(
            filter(None, (dealer.get("Address1", "").strip(), dealer.get("Address2", "").strip()))
        )
        item["city"] = dealer.get("City")
        item["state"] = dealer.get("State")
        item["postcode"] = dealer.get("PostalCode")
        item["lat"] = dealer.get("Lat") or None
        item["lon"] = dealer.get("Lon") or None
        item["country"] = "CA" if dealer.get("State") in CANADIAN_PROVINCES else "US"
        item["phone"] = dealer.get("Phone", "").strip() or None
        email = dealer.get("EMail", "").strip()
        item["email"] = email if email and email.lower() not in SHARED_EMAILS else None
        # The dealer's own site is more specific than the culligan.com landing page.
        if website := dealer.get("WebSite", "").strip():
            item["website"] = website if website.startswith("http") else f"https://{website}"
        else:
            item["website"] = response.url

        oh = OpeningHours()
        for day in DAYS:
            self.add_hours(oh, day, dealer.get(self.hour_fields[day], ""))
        if oh:
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_WATER, item)
        yield item

    def add_hours(self, oh: OpeningHours, day: str, raw: str) -> None:
        raw = raw.strip()
        if not raw or "-" not in raw:
            # Blank, or a non-range value such as "Closed" or "Call for
            # appointment"; the latter is not treated as closed, since it
            # does not necessarily mean the office is unstaffed.
            if raw.lower() == "closed":
                oh.set_closed(day)
            return
        open_time, close_time = (p.strip() for p in raw.split("-", 1))
        open_time = self.normalise_time(open_time, is_close=False)
        close_time = self.normalise_time(close_time, is_close=True)
        if open_time and close_time:
            oh.add_range(day, open_time, close_time)

    @staticmethod
    def normalise_time(raw: str, is_close: bool) -> str | None:
        if not (m := TIME_RE.match(raw)):
            return None
        hour, minute, meridiem = int(m.group(1)), m.group(2), m.group(3)
        if meridiem:
            is_pm = meridiem.lower().startswith("p")
            hour = hour % 12
            if is_pm:
                hour += 12
        elif is_close and hour < 12:
            # A close time given with no AM/PM marker (e.g. "5:00") always
            # means the afternoon for these dealer office hours.
            hour += 12
        return f"{hour:02d}:{minute}"
