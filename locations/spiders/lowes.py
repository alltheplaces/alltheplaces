# -*- coding: utf-8 -*-
import scrapy
import re
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


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
    start_urls = ("https://www.lowes.com/sitemap/store0.xml",)
    download_delay = 0.5

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

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
        ref = re.search(r".+/(.+)", response.url).group(1)

        script_content = response.xpath(
            '//script[contains(text(),"storeHours")]/text()'
        ).extract_first()
        if not script_content:
            return

        # effectively strip off leading "window.__PRELOADED_STATE__ = " where
        # the rest is a json blob
        script_data = script_content.split(" = ", 1)[-1]
        json_data = json.loads(script_data)
        store_hours = json_data.get("storeHours")

        state_texts = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract()
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

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
