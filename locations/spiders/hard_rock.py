import json

import scrapy

from locations.items import Feature


class HardRockSpider(scrapy.Spider):
    name = "hardrock"
    # TODO: has hotels, cafes etc in wikidata, spider will need more work for applying wikidata
    item_attributes = {"brand": "Hard Rock"}
    allowed_domains = ["www.hardrock.com"]
    start_urls = ["https://www.hardrock.com/files/5880/widget935343.js?callback=widget935343DataCallback"]

    def parse(self, response):
        data = json.loads(response.text.replace("widget935343DataCallback(", "").replace(");", ""))
        for location in data.get("PropertyorInterestPoint", []):
            properties = {
                "name": location["interestpointpropertyname"],
                "ref": location["ClassIndex"],
                "street": location["interestpointpropertyaddress"],
                "city": location["interestpointCity"],
                "postcode": location["interestpointPostalCode"],
                "state": location["interestpointStateFullName"],
                "country": location["LocationCountry"],
                "lat": float(location["interestpointinterestlatitude"]),
                "lon": float(location["interestpointinterestlongitude"]),
                "phone": location["interestpointPhoneNumber"],
                "website": location["interestpointMoreInfoLink"],
            }
            yield Feature(**properties)
