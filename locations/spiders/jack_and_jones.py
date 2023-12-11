import re

import scrapy

from locations.items import Feature


class JackAndJonesSpider(scrapy.Spider):
    name = "jack_and_jones"
    item_attributes = {"brand": "Jack & Jones", "brand_wikidata": "Q6077665"}
    start_urls = [
        "https://www.jackjones.com/api/stores/en-se?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-ca?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-fr?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-de?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-nl?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-es?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-be?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-it?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-fi?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-ie?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-pl?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-pl?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-at?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-no?city=&type=json&redirect=false",
        "https://www.jackjones.com/api/stores/en-ch?city=&type=json&redirect=false",
    ]

    def parse(self, response):
        for row in response.json():
            item = Feature()
            item["ref"] = row.get("physicalId")
            item["name"] = row.get("name")
            item["street_address"] = row.get("address", {}).get("street")
            item["city"] = row.get("address", {}).get("city")
            item["postcode"] = row.get("address", {}).get("postalCode")
            item["country"] = re.findall(r"en-[a-z]{2}", response.url)[0][3:].upper()
            item["phone"] = row.get("address", {}).get("phone")
            item["email"] = row.get("address", {}).get("email")
            item["lat"] = row.get("address", {}).get("latitude")
            item["lon"] = row.get("address", {}).get("longitude")

            yield item
