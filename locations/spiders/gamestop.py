import re

import scrapy

from locations.items import Feature


class GamestopSpider(scrapy.Spider):
    name = "gamestop"
    item_attributes = {"brand": "GameStop", "brand_wikidata": "Q202210"}
    allowed_domains = ["www.gamestop.com"]
    start_urls = [
        "https://www.gamestop.ca/StoreLocator/GetStoresForStoreLocatorByProduct",
        "https://www.gamestop.de/StoreLocator/GetStoresForStoreLocatorByProduct",
        "https://www.gamestop.ie/StoreLocator/GetStoresForStoreLocatorByProduct",
        "https://www.gamestop.it/StoreLocator/GetStoresForStoreLocatorByProduct",
        "https://www.gamestop.ch/StoreLocator/GetStoresForStoreLocatorByProduct",
    ]
    requires_proxy = True

    def parse(self, response):
        for data in response.json():
            for key, value in data.items():
                if value == "undefined":
                    data[key] = None

            item = Feature()
            item["name"] = data.get("Name")
            item["street_address"] = data.get("Address")
            item["postcode"] = data.get("Zip")
            item["city"] = data.get("City")
            item["state"] = data.get("Province")
            item["phone"] = data.get("Phones")
            item["email"] = data.get("Email")
            item["lat"] = data.get("Latitude")
            item["lon"] = data.get("Longitude")
            item["country"] = re.findall(r"\.[a-z]{2}/", response.url)[-1][1:3].upper()
            item["ref"] = f'{item["country"]}-{data.get("Id")}'

            yield item
