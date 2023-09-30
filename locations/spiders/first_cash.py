import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class FirstCashSpider(scrapy.Spider):
    name = "first_cash"
    item_attributes = {"brand": "First Cash"}
    allowed_domains = ["find.cashamerica.us"]

    def start_requests(self):
        base_url = "http://find.cashamerica.us/api/stores?p=1&s=100&lat={lat}&lng={lng}&d=2019-10-14T17:43:05.914Z&key=D21BFED01A40402BADC9B931165432CD"

        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

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
