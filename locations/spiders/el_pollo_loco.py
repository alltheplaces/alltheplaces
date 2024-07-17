import scrapy
from scrapy.http import JsonRequest

from locations.items import Feature


class ElPolloLocoSpider(scrapy.Spider):
    name = "el_pollo_loco"
    item_attributes = {"brand": "El Pollo Loco", "brand_wikidata": "Q2353849"}
    allowed_domains = ["www.elpolloloco.com"]
    start_urls = ["https://www.elpolloloco.com/locations/locations_json"]

    def start_requests(self):
        yield JsonRequest(url="https://www.elpolloloco.com/locations/locations_json")

    def parse(self, response):
        store_data = response.json()
        for store in store_data:
            try:
                properties = {
                    "ref": store[0],
                    "street_address": store[1],
                    "city": store[3],
                    "state": store[4],
                    "postcode": store[5],
                    "phone": store[6],
                    "lat": float(store[8]),
                    "lon": float(store[9]),
                }
                yield Feature(**properties)

            except ValueError:
                continue
