import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

day_mapping = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class LowesSpider(scrapy.Spider):
    """ "This spider scrapes Lowes retail store locations"""

    name = "lowes"
    item_attributes = {"brand": "Lowe's", "brand_wikidata": "Q1373493"}
    allowed_domains = ["lowes.com"]
    download_delay = 0.1
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.lowes.com/sitemap/store0.xml",
            callback=self.parse,
        )

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.get("day").get("day")
            open_time = weekday.get("day").get("open")
            hour, minute, sec = open_time.split(".")
            open_time_formatted = hour + ":" + minute

            close = weekday.get("day").get("close")
            hour, minute, sec = close.split(".")
            close_time_formatted = hour + ":" + minute

            if close_time_formatted in {"00:00", "24:00"}:
                close_time_formatted = "23:59"

            opening_hours.add_range(
                day=day_mapping[day],
                open_time=open_time_formatted,
                close_time=close_time_formatted,
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        script_content = response.xpath('//script[contains(text(),"storeHours")]/text()').extract_first()
        if not script_content:
            return

        # effectively strip off leading "window.__PRELOADED_STATE__ = " where
        # the rest is a json blob
        script_data = script_content.split(" = ", 1)[-1]
        json_data = json.loads(script_data)
        store_hours = json_data.get("storeHours")

        properties = {
            "lat": json_data["storeDetails"]["lat"],
            "lon": json_data["storeDetails"]["long"],
            "ref": json_data["storeDetails"]["id"],
            "addr_full": json_data["storeDetails"]["address"],
            "city": json_data["storeDetails"]["city"],
            "state": json_data["storeDetails"]["state"],
            "postcode": json_data["storeDetails"]["zip"],
            "phone": json_data["storeDetails"]["phone"],
            "website": response.request.url,
            "opening_hours": self.parse_hours(store_hours),
            "extras": {
                "amenity:toilets": True,
            },
        }

        yield Feature(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
