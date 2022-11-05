import datetime

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class PandaExpressSpider(scrapy.Spider):
    name = "pandaexpress"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    allowed_domains = ["pandaexpress.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "RETRY_TIMES": 5}

    def start_requests(self):
        today = datetime.date.today().strftime("%Y%m%d")
        nextweek = (datetime.date.today() + datetime.timedelta(days=7)).strftime(
            "%Y%m%d"
        )

        yield scrapy.Request(
            f"https://nomnom-prod-api.pandaexpress.com/restaurants?nomnom=calendars&nomnom_calendars_from={today}&nomnom_calendars_to={nextweek}",
            callback=self.parse_stores,
        )

    def parse_stores(self, response):
        data = response.json()

        for store in data["restaurants"]:
            oh = OpeningHours()
            if len(store.get("calendars").get("calendar")) > 0:
                calendar_ranges = (
                    store.get("calendars").get("calendar")[0].get("ranges")
                )
                for oh_range in calendar_ranges:
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
            yield GeojsonPointItem(**properties)
