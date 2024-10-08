import json

import scrapy

from locations.categories import Categories
from locations.items import Feature


class HardRockSpider(scrapy.Spider):
    name = "hard_rock"
    allowed_domains = ["www.hardrock.com"]
    start_urls = ["https://www.hardrock.com/files/5880/widget935343.js?callback=widget935343DataCallback"]

    cats = {
        "Cafe": {"brand": "Hard Rock Cafe", "brand_wikidata": "Q918151"},
        "Hotel": {"brand": "Hard Rock Hotel", "brand_wikidata": "Q109275902"},
        "Live": {"brand": "Hard Rock Live", "brand_wikidata": "Q5655372", "extras": {"amenity": "music_venue"}},
        "Hotel & Casino": {"brand": "Hard Rock Hotel & Casino", "brand_wikidata": "", "extras": Categories.HOTEL.value},
        "Casino": {"brand": "Hard Rock Casino", "brand_wikidata": "", "extras": {"amenity": "casino"}},
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
                properties.update(cat)
            else:
                self.crawler.stats.inc_value(f'atp/unmapped_category/{location["LocationLocationType"]}')

            yield Feature(**properties)
