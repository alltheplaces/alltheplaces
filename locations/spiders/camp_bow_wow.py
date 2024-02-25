import scrapy

from locations.categories import Categories
from locations.items import Feature


class CampBowWowSpider(scrapy.Spider):
    name = "camp_bow_wow"
    item_attributes = {
        "brand": "Camp Bow Wow",
        "brand_wikidata": "Q121322343",
        "extras": Categories.ANIMAL_BOARDING.value,
    }
    allowed_domains = ["campbowwow.com"]

    def start_requests(self):
        url = "https://www.campbowwow.com/locations/?CallAjax=GetLocations"

        yield scrapy.http.Request(url, method="POST", callback=self.parse)

    def parse(self, response):
        data = response.json()

        for place in data:
            properties = {
                "ref": place["FranchiseLocationID"],
                "name": place["FranchiseLocationName"],
                "street_address": place["Address1"],
                "city": place["City"],
                "state": place["State"],
                "postcode": place["ZipCode"],
                "country": place["Country"],
                "lat": place["Latitude"],
                "lon": place["Longitude"],
                "phone": place["Phone"],
            }

            yield Feature(**properties)
