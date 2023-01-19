import scrapy

from locations.items import Feature


class GamestopSpider(scrapy.Spider):
    name = "gamestop"
    item_attributes = {"brand": "GameStop"}
    allowed_domains = ["www.gamestop.com"]
    start_urls = ["https://www.gamestop.ca/StoreLocator/GetStoresForStoreLocatorByProduct?value=&language=en-CA"]

    def parse(self, response):
        for data in response.json():
            item = Feature()
            item["ref"] = data.get("Id")
            item["name"] = data.get("Name")
            item["postcode"] = data.get("Zip")
            item["city"] = data.get("City")
            item["state"] = data.get("Province")
            item["phone"] = data.get("Phones")
            item["email"] = data.get("Email")
            item["lat"] = data.get("Longitude") if data.get("Longitude") != "undefined" else None
            item["lon"] = data.get("Latitude") if data.get("Latitude") != "undefined" else None
            item["country"] = "CA"

            yield item
