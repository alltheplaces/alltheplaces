# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class WhiteHouseBlackMarketSpider(scrapy.Spider):
    download_delay = 0.2
    name = "whitehouseblackmarket"
    item_attributes = {
        "brand": "White House Black Market",
        "brand_wikidata": "Q7994858",
    }
    allowed_domains = ["whitehouseblackmarket.com"]
    start_urls = ("https://stores.whitehouseblackmarket.com/",)
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        page_numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        template = "https://whitehouse.brickworksoftware.com/locations_search?esSearch=%7B%22page%22:{page},%22storesPerPage%22:50,%22domain%22:%22whitehouse.brickworksoftware.com%22%7D"

        headers = {
            "Accept": "application/json",
        }

        for page in page_numbers:
            yield scrapy.http.FormRequest(
                url=template.format(page=page),
                method="GET",
                headers=headers,
                callback=self.parse,
            )

    def parse(self, response):
        jsonresponse = response.json()
        data = jsonresponse["hits"]
        for stores in data:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "name": store_data["attributes"]["name"],
                "ref": store_data["id"],
                "addr_full": store_data["attributes"]["address1"],
                "city": store_data["attributes"]["city"],
                "state": store_data["attributes"]["state"],
                "postcode": store_data["attributes"]["postalCode"],
                "country": store_data["attributes"]["countryCode"],
                "phone": store_data["attributes"]["phoneNumber"],
                "lat": float(store_data["attributes"]["latitude"]),
                "lon": float(store_data["attributes"]["longitude"]),
            }

            hours = store_data["relationships"]["hours"]

            if hours:
                properties["opening_hours"] = self.process_hours(hours)

            yield GeojsonPointItem(**properties)

    def process_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            hr = json.dumps(hour)
            hrs = json.loads(hr)
            day = hrs["displayDay"]
            open_time = hrs["displayStartTime"].strip(" ")
            close_time = hrs["displayEndTime"].strip(" ")

            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M%p",
            )
        return opening_hours.as_opening_hours()
