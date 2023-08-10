import scrapy

from locations.items import Feature


class PortillosSpider(scrapy.Spider):
    name = "portillos"
    item_attributes = {"brand": "Portillo's", "brand_wikidata": "Q3399307"}
    allowed_domains = ["www.portillos.com"]
    start_urls = ("https://www.portillos.com/locations/",)

    def parse(self, response):
        yield scrapy.Request(
            "https://www.portillos.com/ajax/location/getAllLocations/",
            callback=self.parse_locations,
            method="POST",
            body='{"locations":[],"all":"y"}',
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json",
                "s": "mjA1AiWID8JqImr3iMoEXFUpeuasRBIglY+FBqETplI=",
            },
        )

    def parse_locations(self, response):
        data = response.json()

        for location in data["locations"]:
            yield scrapy.Request(
                "https://www.portillos.com/ajax/location/getLocationDetails/?id=%s" % location["Id"],
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store_data = response.json()["location"]

        properties = {
            "phone": store_data["Phone"],
            "website": response.urljoin(store_data["Url"]),
            "ref": store_data["Id"],
            "name": store_data["Name"],
            "street_address": store_data["Address"],
            "postcode": store_data["Zip"],
            "state": store_data["State"],
            "city": store_data["City"],
            "lon": float(store_data["Lng"]),
            "lat": float(store_data["Lat"]),
        }

        yield Feature(**properties)
