import re

import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsSGSpider(scrapy.Spider):
    name = "mcdonalds_sg"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.com.sg"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    start_urls = ("https://www.mcdonalds.com.sg/wp/wp-admin/admin-ajax.php?action=store_locator_locations",)

    def store_hours(self, data):
        if data == "24 hours":
            return 24 / 7
        match = re.sub("<[^<]+?>", "", data)
        return " ".join(match.split())

    def parse_address(self, data):
        match = re.sub("<[^<]+?>", "", data)
        return " ".join(match.split())

    def parse(self, response):
        stores = response.json()
        for data in stores:
            properties = {
                "city": data["city"],
                "ref": data["id"],
                "phone": data["phone"],
                "state": data["region"],
                "postcode": data["zip"],
                "name": data["name"],
                "lat": data["lat"],
                "lon": data["long"],
            }

            address = self.parse_address(data["address"])
            if address:
                properties["addr_full"] = address

            opening_hours = self.store_hours(data["op_hours"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield Feature(**properties)
