from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class RocketUSSpider(Spider):
    name = "rocket_us"
    item_attributes = {"brand": "Rocket", "brand_wikidata": "Q121513516"}
    start_urls = ["https://rocketstores.com/wp-json/stations/v1/locations"]

    def parse(self, response, **kwargs):
        for location in response.json()["stations"]:
            item = Feature()
            item["ref"] = location["ID"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["store_name"]
            item["street_address"] = location["address"]
            item["city"] = location["city"]
            item["state"] = location["state"]
            item["postcode"] = location["zip"]
            item["country"] = location["country"]
            item["phone"] = location["phone_number"]
            item["located_in"] = location["brand"]["name"]

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
