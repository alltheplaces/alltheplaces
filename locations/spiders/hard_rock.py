import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class HardRockSpider(scrapy.Spider):
    name = "hard_rock"
    allowed_domains = ["www.hardrock.com"]
    start_urls = ["https://www.hardrock.com/files/5880/widget935343.js?callback=widget935343DataCallback"]

    cats = {
        "Cafe": ({"brand": "Hard Rock Cafe", "brand_wikidata": "Q918151"}, Categories.RESTAURANT),
        "Hotel": ({"brand": "Hard Rock Hotel", "brand_wikidata": "Q109275902"}, Categories.HOTEL),
        "Live": ({"brand": "Hard Rock Live", "brand_wikidata": "Q5655372"}, Categories.MUSIC_VENUE),
        "Hotel & Casino": ({"brand": "Hard Rock Hotel & Casino"}, Categories.HOTEL),
        "Casino": ({"brand": "Hard Rock Casino"}, Categories.CASINO),
    }

    def parse(self, response):
        data = json.loads(response.text.replace("widget935343DataCallback(", "").replace(");", ""))
        for location in data.get("PropertyorInterestPoint", []):
            properties = {
                "name": location["interestpointpropertyname"],
                "ref": location["ClassIndex"],
                "street_address": location["interestpointpropertyaddress"],
                "city": location["interestpointCity"],
                "postcode": location["interestpointPostalCode"],
                "state": location["interestpointState"],
                "country": location["LocationCountry"],
                "lat": float(location["interestpointinterestlatitude"]),
                "lon": float(location["interestpointinterestlongitude"]),
                "phone": location["interestpointPhoneNumber"],
                "website": location["interestpointMoreInfoLink"],
            }
            if cat := self.cats.get(location["LocationLocationType"]):
                properties.update(cat[0])
                apply_category(cat[1], properties)
            else:
                self.logger.error("Unexpected type: {}".format(location["LocationLocationType"]))

            yield Feature(**properties)
