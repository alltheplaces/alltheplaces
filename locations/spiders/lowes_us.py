import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import FIREFOX_LATEST


class LowesUSSpider(SitemapSpider):
    name = "lowes_us"
    item_attributes = {"brand": "Lowe's", "brand_wikidata": "Q1373493"}
    allowed_domains = ["lowes.com"]
    sitemap_urls = ["https://www.lowes.com/sitemap/store0.xml"]
    sitemap_rules = [(r"^https://www.lowes.com/store", "parse_store")]
    user_agent = FIREFOX_LATEST
    requires_proxy = True

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
                day=day[:2],
                open_time=open_time_formatted,
                close_time=close_time_formatted,
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        script_content = response.xpath('//script[contains(text(),"storeHours")]/text()').extract_first()
        if not script_content:
            return

        # effectively strip off leading "window.__FRAGMENT__FOOTER__PRELOAD__ = " where
        # the rest is a json blob
        script_data = script_content.split(" = ", 1)[-1]
        json_data = json.loads(script_data)
        store_hours = json_data.get("storeHours")

        properties = {
            "lat": json_data["storeDetails"]["lat"],
            "lon": json_data["storeDetails"]["long"],
            "ref": json_data["storeDetails"]["id"],
            "street_address": json_data["storeDetails"]["address"],
            "city": json_data["storeDetails"]["city"],
            "state": json_data["storeDetails"]["state"],
            "postcode": json_data["storeDetails"]["zip"],
            "phone": json_data["storeDetails"]["phone"],
            "website": response.request.url,
            "opening_hours": self.parse_hours(store_hours),
            "extras": {},
        }

        if start_date := json_data["storeDetails"].get("openDate"):
            properties["extras"]["start_date"] = start_date

        yield Feature(**properties)
