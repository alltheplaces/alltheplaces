import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address
from locations.user_agents import BROWSER_DEFAULT

class LittleCaesarsUSSpider(Spider):
    name = "little_caesars_us"
    item_attributes = {
        "brand": "Little Caesars",
        "brand_wikidata": "Q1393809",
    }
    allowed_domains = ["api.cloud.littlecaesars.com"]
    download_delay = 0.1

    def start_requests(self):
        for record in postal_regions("US"):
            headers = {
                "Origin": "https://littlecaesars.com",
                "Referer": "https://littlecaesars.com/",
            }
            data = {
                "address": {
                    "city": "",
                    "state": "",
                    "street" : "",
                    "zip": str(record["postal_region"]),
                }
            }
            yield JsonRequest(url="https://api.cloud.littlecaesars.com/bff/api/GetClosestStores", data=data, headers=headers, method="POST", callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["stores"]:
            store_id = str(location["locationNumber"])
            yield JsonRequest(url="https://api.cloud.littlecaesars.com/bff/api/v2/store/location/{store_id}", callback=self.parse_store)

    def parse_store(self, response):
        location = response.json()["storeInfo"]
        item = DictParser.parse(location)
        item["street_address"] = ", ".join(filter(None, [location.get("address1"), location.get("address2")]))
        yield item
