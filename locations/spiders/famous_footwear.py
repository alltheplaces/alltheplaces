# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem
from urllib.parse import urlencode


class FamousFootwearSpider(scrapy.Spider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear"}
    allowed_domains = ["www.famousfootwear.com"]
    start_urls = [
        "www.famousfootwear.com",
    ]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
    }

    def start_requests(self):
        url = "https://www.famousfootwear.com/Stores/Store/FindStoresNearby?"

        with open("./locations/searchable_points/us_zcta.csv") as postal_codes:
            next(postal_codes)  # Ignore the header
            for postal_code in postal_codes:
                row = postal_code.split(",")
                post_code = row[0].strip().strip('"')

                params = {"zipcode": post_code, "radius": "100"}

                yield scrapy.http.Request(url + urlencode(params), callback=self.parse)

    def parse(self, response):
        data = response.json()
        stores = data["stores"]

        for store in stores:
            properties = {
                "ref": store["storeNumber"],
                "name": store["address1"],
                "addr_full": store["address2"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": store["country"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phoneNumber"],
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
