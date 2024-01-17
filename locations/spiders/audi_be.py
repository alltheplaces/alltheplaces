from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class AudiBESpider(Spider):
    name = "audi_be"
    item_attributes = {"brand": "Audi", "brand_wikidata": "Q23317"}
    allowed_domains = ["dealerlocator-api.dieteren.be"]
    start_urls = ["https://dealerlocator-api.dieteren.be/api/workLocations?templateId=16&language=fr"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["Dealers"]:
            properties = {
                "ref": location.get("WorkLocationId"),
                "name": location.get("NAME"),
                "street_address": location.get("ADDRESS"),
                "city": location.get("CITY"),
                "postcode": location.get("ZIP"),
                "lat": float(location.get("GPSLAT")),
                "lon": float(location.get("GPSLONG")),
                "phone": location.get("TEL"),
                "website": location.get("URL"),
            }
            if properties["website"] and properties["website"].startswith("www."):
                properties["website"] = "https://" + properties["website"]
            apply_category(Categories.SHOP_CAR, properties)
            yield Feature(**properties)
