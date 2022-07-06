import scrapy
import re
from locations.items import GeojsonPointItem


class NikeSpider(scrapy.Spider):
    name = "nike"
    item_attributes = {"brand": "Nike"}
    allowed_domains = ["storeviews-cdn.risedomain-prod.nikecloud.com"]
    download_delay = 0.3

    def start_requests(self):
        url = "https://storeviews-cdn.risedomain-prod.nikecloud.com/store-locations-static.json"

        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        store = response.json()
        all_stores = store["stores"]

        for store in all_stores:
            store = all_stores.get(store)
            addresses = store.get("address")
            coords = store.get("coordinates")

            addr_1 = addresses.get("address_1")
            addr_2 = addresses.get("address_2")
            addr_3 = addresses.get("address_3")

            properties = {
                "name": store.get("name"),
                "ref": store.get("id"),
                "addr_full": re.sub(
                    " +", " ", " ".join(filter(None, [addr_1, addr_2, addr_3])).strip()
                ),
                "city": addresses.get("city"),
                "state": addresses.get("state"),
                "postcode": store.get("postalCode"),
                "country": addresses.get("country"),
                "phone": store.get("phone"),
                "website": response.url,
                "lat": coords.get("latitude"),
                "lon": coords.get("longitude"),
                "extras": {
                    "store_type": store.get("facilityType"),
                },
            }

            yield GeojsonPointItem(**properties)
