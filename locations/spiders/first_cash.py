import scrapy
from scrapy.http import JsonRequest

from locations.geo import point_locations
from locations.items import Feature


class FirstCashSpider(scrapy.Spider):
    name = "first_cash"
    item_attributes = {"brand": "First Cash", "brand_wikidata": "Q5048636"}
    allowed_domains = ["find.cashamerica.us"]

    def start_requests(self):
        base_url = "http://find.cashamerica.us/api/stores?p=1&s=100&lat={lat}&lng={lng}&d=2019-10-14T17:43:05.914Z&key=D21BFED01A40402BADC9B931165432CD"

        for lat, lon in point_locations("us_centroids_100mile_radius.csv"):
            yield JsonRequest(url=base_url.format(lat=lat, lng=lon))

    def parse(self, response):
        data = response.json()

        for place in data:
            properties = {
                "ref": place["storeNumber"],
                "name": place["shortName"],
                "street_address": place["address"]["address1"],
                "city": place["address"]["city"],
                "state": place["address"]["state"],
                "postcode": place["address"]["zipCode"],
                "country": "US",
                "lat": place["latitude"],
                "lon": place["longitude"],
                "phone": place["phone"],
                "brand": place["brand"].split(" #")[0],
            }

            yield Feature(**properties)
