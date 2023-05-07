import json
import re

import scrapy

from locations.items import Feature

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class HarristeeterSpider(scrapy.Spider):
    name = "harristeeter"
    item_attributes = {"brand": "Harris Teeter"}
    allowed_domains = ["harristeeter.com"]
    start_urls = ("https://www.harristeeter.com/store/#/app/store-locator",)

    handle_httpstatus_list = [401]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        }
    }

    def store_hours(self, store_hours):
        res = ""
        for day in store_hours:
            match = re.search(
                r"(\w*)(\s*-\s*(\w*))?\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)?\s*-\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)",
                day.replace("Midnight", "12:00pm"),
            )

            if not match:
                continue
            res += match[1][:2]

            try:
                res += match[2].replace(" ", "")[:3] + " "
            except Exception:
                res += " "

            if match[5]:
                first_minutes = match[5]
            else:
                first_minutes = ":00"

            if match[9]:
                second_minutes = match[9]
            else:
                second_minutes = ":00"

            res += str(int(match[4]) + (12 if match[7] in ["pm", "mp"] else 0)) + first_minutes + "-"
            res += str(int(match[8]) + (12 if match[10] in ["pm", "mp"] else 0)) + second_minutes + ";"

        return res.rstrip(";").strip()

    def parse(self, response):
        yield scrapy.Request(
            "https://www.harristeeter.com/api/checkLogin",
            method="POST",
            callback=self.check_login,
        )

    def check_login(self, response):
        yield scrapy.Request(
            "https://www.harristeeter.com/store/#/app/store-locator",
            callback=self.get_store_locator,
        )

    def get_store_locator(self, response):
        yield scrapy.Request(
            "https://www.harristeeter.com/api/v1/stores/search?Address=98011&Radius=20000&AllStores=true",
            callback=self.parse_shop,
        )

    def parse_shop(self, response):
        shops = json.loads(response.text)["Data"]

        for shop in shops:
            props = {
                "ref": shop["StoreNumber"],
                "addr_full": shop["Street"],
                "city": shop.get("City"),
                "state": shop.get("State"),
                "postcode": shop.get("PostalCode"),
                "country": shop["Country"],
                "name": shop["StoreName"],
                "phone": shop["Telephone"],
                "lat": float(shop["Latitude"]),
                "lon": float(shop["Longitude"]),
                "opening_hours": shop["StoreHours"].replace("Open 24 Hours", "Mo-Su 0:00-24:00"),
            }

            yield Feature(**props)
