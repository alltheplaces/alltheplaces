import re

import scrapy
from scrapy.spiders import SitemapSpider
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap

from locations.hours import OpeningHours
from locations.items import Feature


class PotbellySandwichShopSpider(SitemapSpider):
    name = "potbelly_sandwich_shop"
    item_attributes = {"brand": "Potbelly", "brand_wikidata": "Q7234777"}
    allowed_domains = ["www.potbelly.com", "api.prod.potbelly.com"]
    sitemap_urls = [
        "https://www.potbelly.com/sitemap_locations.xml",
    ]

    def _parse_sitemap(self, response):
        # Location pages are never fetched: the API can be queried directly using a
        # slug parsed out of each sitemap URL, so bypass the default per-URL requests.
        for url in iterloc(Sitemap(self._get_sitemap_body(response))):
            if m := re.search("/locations/[^/]+/([^/]+)", url):
                slug = m[1]
                api_url = f"https://api.prod.potbelly.com/v1/restaurants/byslug/{slug}?includeHours=true"
                yield scrapy.Request(api_url, callback=self.parse_store)

    def parse_store(self, response):
        store = response.json()

        oh = OpeningHours()
        if calendars := store.get("calendars"):
            # Look for the first calendar showing "business hours"
            business_hours_calendar = next(filter(lambda c: c["type"] == "business", calendars))

            calendar_ranges = business_hours_calendar.get("ranges")
            first_day_seen = None
            for oh_range in calendar_ranges:
                # The calendar includes multiple weeks of hours, so break out of the loop if we see the same day again
                if first_day_seen and first_day_seen == oh_range.get("weekday"):
                    break
                elif not first_day_seen:
                    first_day_seen = oh_range.get("weekday")

                oh.add_range(
                    oh_range.get("weekday")[:2],
                    oh_range.get("start").split(" ")[-1],
                    oh_range.get("end").split(" ")[-1],
                    time_format="%H:%M",
                )

        properties = {
            "ref": store["id"],
            "lat": store["latitude"],
            "lon": store["longitude"],
            "name": store["name"],
            "street_address": store["streetaddress"],
            "opening_hours": oh,
            "city": store["city"],
            "state": store["state"],
            "postcode": store["zip"],
            "country": store["country"],
            "phone": store["telephone"],
            "extras": {
                "delivery": "yes" if store["candeliver"] else "no",
                "takeaway": "yes" if store["canpickup"] else "no",
                "drive_through": "yes" if store["supportsdrivethru"] else "no",
            },
        }

        yield Feature(**properties)
