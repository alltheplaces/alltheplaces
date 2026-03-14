import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class CrewCarwashUSSpider(scrapy.Spider):
    name = "crew_carwash_us"
    item_attributes = {"brand": "Crew Carwash"}
    allowed_domains = ["crewcarwash.com"]
    # Request up to 100 items (WP REST API limits per_page; 58 locations require more than the default 10)
    start_urls = ("https://crewcarwash.com/wp-json/wp/v2/locations?per_page=100",)

    def parse_hours(self, hours_raw: str) -> str | None:
        if not hours_raw:
            return None

        s = hours_raw.strip()
        # remove common prefixes like 'Exterior Wash:' or 'Interior Wash:'
        s = re.sub(r"^[A-Za-z\s]+:\s*", "", s)

        # look for a 12h time range like '7am to 8pm' or '7:00am - 8:00pm'
        m = re.search(
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*(?:to|-|–|—)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)", s
        )
        if not m:
            return None

        open_t = m.group(1).upper().replace(" ", "")
        close_t = m.group(2).upper().replace(" ", "")

        # normalize times to include minutes
        if ":" not in open_t:
            open_t = open_t.replace("AM", ":00AM").replace("PM", ":00PM")
        if ":" not in close_t:
            close_t = close_t.replace("AM", ":00AM").replace("PM", ":00PM")

        oh = OpeningHours()
        # add for every day
        try:
            for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                oh.add_range(d, open_t, close_t, time_format="%I:%M%p")
        except Exception:
            return None

        return oh.as_opening_hours()

    def parse(self, response):
        for row in response.json():
            acf = row.get("acf", {})
            lat = acf.get("latitude") or acf.get("lat") or acf.get("latitude")
            lon = acf.get("longitude") or acf.get("lng") or acf.get("longitude")

            addr_parts = []
            if acf.get("street_address"):
                addr_parts.append(acf.get("street_address"))
            if acf.get("city"):
                addr_parts.append(acf.get("city"))
            if acf.get("state"):
                addr_parts.append(acf.get("state"))
            if acf.get("zip_code"):
                addr_parts.append(acf.get("zip_code"))

            opening_hours = self.parse_hours(acf.get("hours") or "")

            properties = {
                "ref": row.get("id"),
                "lat": lat,
                "lon": lon,
                "website": row.get("link") or acf.get("location_link"),
                "name": row.get("title", {}).get("rendered"),
                "addr_full": ", ".join(addr_parts) if addr_parts else None,
                "phone": acf.get("phone_number") or acf.get("phone"),
                "opening_hours": opening_hours,
            }

            item = Feature(**properties)
            # move the title into branch
            item["branch"] = item.pop("branch", None)

            apply_category(Categories.CAR_WASH, item)
            yield item
