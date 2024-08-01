import scrapy
from scrapy.http import JsonRequest

from locations.items import Feature


class WinnDixieSpider(scrapy.Spider):
    name = "winn_dixie"
    item_attributes = {"brand": "Winn Dixie", "brand_wikidata": "Q1264366"}
    allowed_domains = ["winndixie.com"]

    def start_requests(self):
        yield JsonRequest(
            url="https://www.winndixie.com/V2/storelocator/getStores?search=jacksonville,%20fl&strDefaultMiles=1000&filter=",
        )

    def parse(self, response):
        jsonresponse = response.json()
        for store in jsonresponse:
            properties = {
                "name": store["StoreName"],
                "ref": store["StoreCode"],
                "addr_full": store["Address"]["AddressLine2"],
                "city": store["Address"]["City"],
                "state": store["Address"]["State"],
                "postcode": store["Address"]["Zipcode"],
                "country": store["Address"]["Country"],
                "phone": store["Phone"],
                "lat": float(store["Location"]["Latitude"]),
                "lon": float(store["Location"]["Longitude"]),
            }
            slug = f'{properties["city"]}/{properties["state"]}?search={properties["ref"]}'.lower()
            properties["website"] = f"https://www.winndixie.com/storedetails/{slug}"

            yield Feature(**properties)
