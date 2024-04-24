import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.items import Feature


class HarveysSupermarketsUSSpider(scrapy.Spider):
    # Note: This is winndixie and harveys are owned by the same parent (Southeastern Grocers: https://www.segrocers.com/)
    # and appear to use the same APIs.
    # At a later point we may consolidate the spiders
    name = "harveys_supermarkets_us"
    item_attributes = {
        "brand": "Harveys Supermarkets",
        "brand_wikidata": "Q5677767",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["harveyssupermarkets.com"]

    def start_requests(self):
        yield JsonRequest(
            url="https://www.harveyssupermarkets.com/V2/storelocator/getStores?search=jacksonville,%20fl&strDefaultMiles=1000&filter=",
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
            properties["website"] = f"https://www.harveyssupermarkets.com/storedetails/{slug}"

            yield Feature(**properties)
