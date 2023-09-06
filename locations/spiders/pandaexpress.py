import datetime

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class PandaExpressSpider(scrapy.Spider):
    name = "pandaexpress"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    allowed_domains = ["pandaexpress.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "RETRY_TIMES": 10}
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def start_requests(self):
        today = datetime.date.today().strftime("%Y%m%d")
        nextweek = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y%m%d")

        yield scrapy.Request(
            f"https://nomnom-prod-api.pandaexpress.com/restaurants?nomnom=calendars&nomnom_calendars_from={today}&nomnom_calendars_to={nextweek}",
            callback=self.parse_stores,
        )

    def parse_stores(self, response):
        data = response.json()

        for store in data["restaurants"]:
            oh = OpeningHours()
            if len(store.get("calendars").get("calendar")) > 0:
                calendar_ranges = store.get("calendars").get("calendar")[0].get("ranges")
                for oh_range in calendar_ranges:
                    oh.add_range(
                        oh_range.get("weekday")[:2],
                        oh_range.get("start").split(" ")[-1],
                        oh_range.get("end").split(" ")[-1],
                        time_format="%H:%M",
                    )
            slug = (
                "/".join([store["state"], store["city"], store["streetaddress"]])
                .lower()
                .replace(".", "")
                .replace(" ", "-")
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
                "website": f"https://www.pandaexpress.com/locations/{slug}",
            }
            yield Feature(**properties)
