import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class VerizonUSSpider(scrapy.Spider):
    name = "verizon_us"
    item_attributes = {"brand": "Verizon", "brand_wikidata": "Q919641"}
    allowed_domains = ["www.verizonwireless.com"]
    start_urls = ["https://www.verizonwireless.com/sitemap_storelocator.xml"]
    user_agent = BROWSER_DEFAULT

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for store_day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            open_time = store_hours.get(f"{store_day}Open")
            close_time = store_hours.get(f"{store_day}Close")

            if open_time and close_time and open_time.lower() != "closed" and close_time.lower() != "closed":
                opening_hours.add_range(
                    day=store_day[0:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()

        for url in urls:
            if url.split("/")[-2].split("-")[-1].isdigit():
                # Store pages have a number at the end of their URL
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        script = response.xpath('//script[contains(text(), "storeJSON")]/text()').extract_first()
        if not script:
            return

        store_data = json.loads(re.search(r"var storeJSON = (.*);", script).group(1))

        properties = {
            "name": store_data["storeName"],
            "ref": store_data["storeNumber"],
            "street_address": store_data["address"]["streetAddress"],
            "city": store_data["address"]["addressLocality"],
            "state": store_data["address"]["addressRegion"],
            "postcode": store_data["address"]["postalCode"],
            "country": store_data["address"]["addressCountry"],
            "phone": store_data.get("telephone"),
            "website": response.url,
            "lat": store_data["geo"].get("latitude"),
            "lon": store_data["geo"].get("longitude"),
            "extras": {
                # Sometimes 'postStoreDetail' exists with "None" value, usual get w/ default syntax isn't reliable
                "operator": (store_data.get("posStoreDetail") or {}).get("businessName"),
                "retail_id": store_data.get("retailId"),
                "store_type": (store_data.get("posStoreDetail") or {}).get("storeType"),
                "store_type_note": ";".join(store_data.get("typeOfStore")),
            },
        }

        hours = self.parse_hours(store_data.get("StoreHours"))
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)
