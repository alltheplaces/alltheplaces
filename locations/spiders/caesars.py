import scrapy

from locations.items import Feature


class CaesarsSpider(scrapy.Spider):
    name = "caesars"
    item_attributes = {"brand": "Caesars Entertainment", "brand_wikidata": "Q18636524", "extras": {"amenity": "casino"}}
    start_urls = ["https://www.caesars.com/api/v1/properties"]

    def parse(self, response):
        stores = response.json()
        for store in stores:
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "street_address": store.get("address").get("street"),
                "city": store.get("address").get("city"),
                "state": store.get("address").get("state"),
                "postcode": store.get("address").get("zip"),
                "country": "US",
                "phone": store.get("phone"),
                "lat": float(store["location"]["latitude"]),
                "lon": float(store["location"]["longitude"]),
                "website": store.get("url"),
                "extras": {"type": store["brand"]},
            }

            yield Feature(**properties)
