import re

import scrapy

from locations.items import Feature


class ChuysSpider(scrapy.Spider):
    name = "chuys"
    allowed_domains = ["www.chuys.com"]
    item_attributes = {"brand": "Chuy's", "brand_wikidata": "Q5118415"}
    start_urls = ["https://www.chuys.com/api/locations.json"]

    def parse(self, response):
        for data in response.json().get("locations"):
            properties = {
                "ref": data.get("id"),
                "addr_full": data.get("address", {}).get("address"),
                "housenumber": data.get("address", {}).get("parts", {}).get("number"),
                "street_address": data.get("address").get("parts", {}).get("address"),
                "postcode": data.get("address", {}).get("parts", {}).get("postcode"),
                "city": data.get("address", {}).get("parts", {}).get("city"),
                "state": (re.findall("[A-Z]{2}", data.get("address", {}).get("address"))[0:1] or (None,))[0],
                "website": data.get("url"),
                "lat": data.get("address", {}).get("lat"),
                "lon": data.get("address", {}).get("lng"),
                "phone": data.get("phoneNumber", {}).get("text") if data.get("phoneNumber") else None,
            }

            yield Feature(**properties)
