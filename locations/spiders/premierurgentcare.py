# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class DifferentHours(Exception):
    pass


class PremierurgentcareSpider(scrapy.Spider):
    name = "premierurgentcare"
    item_attributes = {"brand": "Premier Urgent Care"}
    allowed_domains = ["premierimc.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "http://www.premierimc.com/wp-admin/admin-ajax.php?action=store_search&lat=40.030628&lng=-75.36398400000002&max_results=50&search_radius=10&autoload=1",
    )

    def parse(self, response):
        jsonresponse = response.json()

        for store in jsonresponse:
            addr_full = (
                store["address"]
                + ", "
                + store["city"]
                + " "
                + store["state"]
                + " "
                + store["zip"]
            )
            datestring = store["hours"]
            hour_match = re.findall(r"(\d{1,2}:\d{1,2})", datestring)

            for hour in hour_match:
                if hour == "9:00":
                    pass
                else:
                    raise DifferentHours(
                        "Store added with different hours than 09:00-21:00"
                    )

            properties = {
                "name": store["store"],
                "addr_full": addr_full,
                "street": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": store["country"],
                "phone": store["phone"],
                "website": store["permalink"],
                "opening_hours": "09:00-21:00",
                "ref": store["id"] + " " + store["store"],
                "lat": float(store["lat"]),
                "lon": float(store["lng"]),
            }

            yield GeojsonPointItem(**properties)
