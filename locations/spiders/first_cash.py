import scrapy
from scrapy import Request
from scrapy.http import JsonRequest

from locations.items import Feature


class FirstCashSpider(scrapy.Spider):
    name = "first_cash"
    item_attributes = {"brand": "First Cash", "brand_wikidata": "Q5048636"}
    allowed_domains = ["find.cashamerica.us"]

    def make_request(self, page: int = 1) -> Request:
        return JsonRequest(
            url="http://find.cashamerica.us/api/stores?p={page}&s=100&lat={lat}&lng={lng}&d=2019-10-14T17:43:05.914Z&key=D21BFED01A40402BADC9B931165432CD".format(
                page=page, lat=38.8, lng=-107.1
            ),
            meta={"page": page},
        )

    def start_requests(self):
        yield self.make_request()

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

        if len(data) == 100:
            yield self.make_request(response.meta["page"] + 1)
