import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAYS = [
    "Monday",
    "Tuesday",
    "Wednsday",  # sic
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class EightyfourLumberUSSpider(scrapy.Spider):
    name = "eightyfour_lumber_us"
    item_attributes = {"brand": "84 Lumber", "brand_wikidata": "Q4644779"}
    allowed_domains = ["84lumber.com"]

    start_urls = ["https://www.84lumber.com/umbraco/surface/StoreSupport/StoreSearch?radius=10000"]

    def parse(self, response):
        data = json.loads(json.loads(response.text))
        for row in data:
            opening_hours = OpeningHours()
            for day in DAYS:
                if not row[f"{day}HoursCheck"]:
                    continue
                open_time = row[f"{day}OpenHours"]
                close_time = row[f"{day}CloseHours"]
                opening_hours.add_range(day[:2], open_time, close_time, "%I:%M%p")
            properties = {
                "ref": row["StoreNumber"],
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "name": row["Name"],
                "website": f'https://www.84lumber.com/store-locator/store-detail/?storeId={row["StoreNumber"]}',
                "street_address": row["Address"],
                "city": row["City"],
                "state": row["State"],
                "postcode": row["Zip"],
                "phone": row["Phone"],
                "opening_hours": opening_hours.as_opening_hours(),
            }
            yield Feature(**properties)
