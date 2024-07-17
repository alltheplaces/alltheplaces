import json
import re

import scrapy

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class FreshMarketSpider(scrapy.Spider):
    name = "fresh_market"
    item_attributes = {
        "brand": "Fresh Market",
        "brand_wikidata": "Q7735265",
        "country": "US",
    }
    allowed_domains = ["thefreshmarket.com"]
    start_urls = ("https://www.thefreshmarket.com/your-market/store-locator/",)

    def parse(self, response):
        json_data = response.xpath(
            '//script[@charset="UTF-8"][@data-reactid][contains(., "stores")]/text()'
        ).get()  # JS not JSON
        match = re.search(r'\],"allStores":(\[.+\]),"data":', json_data)
        if not match:
            return
        all_stores = json.loads(match.group(1))
        for store in all_stores:
            properties = {
                "name": store["storeName"],
                "ref": store["storeNumber"],
                "street_address": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postalCode"],
                "phone": store["phoneNumber"],
                "website": "https://www.thefreshmarket.com/my-market/store/" + store["slug"],
                "lat": float(store["storeLocation"]["lat"]),
                "lon": float(store["storeLocation"]["lon"]),
            }

            oh = OpeningHours()
            for start_day, end_day, start_time, end_time in re.findall(
                r"(\w{3})-(\w{3}): (\d(?:am|pm))-(\d(?:am|pm))", store["moreStoreHours"]
            ):
                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)
                for day in day_range(start_day, end_day):
                    oh.add_range(day, start_time, end_time, time_format="%I%p")
            properties["opening_hours"] = oh.as_opening_hours()

            yield Feature(**properties)
