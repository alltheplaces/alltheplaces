import scrapy
from scrapy.http import JsonRequest

from locations.geo import point_locations
from locations.items import Feature


class HoneyBakedHamSpider(scrapy.Spider):
    name = "honey_baked_ham"
    item_attributes = {"brand": "Honey Baked Ham", "brand_wikidata": "Q5893363"}
    allowed_domains = ["honeybaked.com"]
    start_urls = ("https://www.honeybaked.com/stores",)

    def parse(self, response):
        for lat, lon in point_locations("us_centroids_100mile_radius.csv"):
            yield JsonRequest(
                f"https://www.honeybaked.com/api/store/v1/?long={lon}&lat={lat}&radius=250", callback=self.parse_search
            )

    def parse_search(self, response):
        data = response.json()

        for i in data:
            properties = {
                "ref": i["storeInformation"]["storeId"],
                "name": i["storeInformation"]["displayName"],
                "street_address": i["storeInformation"]["address1"],
                "city": i["storeInformation"]["city"],
                "state": i["storeInformation"]["state"],
                "postcode": i["storeInformation"]["zipCode"],
                "country": i["storeInformation"]["countryCode"],
                "phone": i["storeInformation"]["phoneNumber"],
                "website": f'https://www.honeybaked.com/stores/{i["storeInformation"]["storeId"]}',
                "email": i["storeInformation"]["storeEmail"],
                "facebook": i["storeInformation"]["facebookUrl"],
                "lat": float(i["storeInformation"]["location"]["coordinates"][1]),
                "lon": float(i["storeInformation"]["location"]["coordinates"][0]),
            }
            yield Feature(**properties)
