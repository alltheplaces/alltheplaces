import datetime
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class FreddysSpider(scrapy.Spider):
    name = "freddys"
    item_attributes = {"brand": "Freddy's", "brand_wikidata": "Q5496837"}
    allowed_domains = ["freddys.com"]
    download_delay = 0.75

    start_urls = [
        "https://www.freddys.com/sitemap.xml",
    ]

    def parse(self, response):
        today = datetime.date.today().strftime("%Y%m%d")
        nextweek = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y%m%d")
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if m := re.search("/location/([^/]+)/", url):
                slug = m[1]
                url = f"https://nomnom-prod-api.freddys.com/restaurants/byslug/{slug}?nomnom=calendars&nomnom_calendars_from={today}&nomnom_calendars_to={nextweek}&nomnom_exclude_extref=999"
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        store = response.json()

        oh = OpeningHours()
        if calendars := store.get("calendars").get("calendar"):
            # Look for the first calendar showing "business hours"
            business_hours_calendar = next(filter(lambda c: c["type"] == "business", calendars))

            calendar_ranges = business_hours_calendar.get("ranges")
            first_day_seen = None
            for oh_range in calendar_ranges:
                # The calendar may include multiple weeks of hours, so break out of the loop if we see the same day again
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
            "opening_hours": oh.as_opening_hours(),
            "city": store["city"],
            "state": store["state"],
            "postcode": store["zip"],
            "country": store["country"],
            "phone": store["telephone"],
        }

        yield Feature(**properties)
