import scrapy
import re
from locations.items import GeojsonPointItem


class NikeSpider(scrapy.Spider):
    name = "nike"
    item_attributes = {"brand": "Nike"}
    allowed_domains = ["nike.bricksoftware.com"]
    download_delay = 0.3

    def start_requests(self):
        url = "https://nike.brickworksoftware.com/api/v3/stores.json"

        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.json()
        stores = data["stores"]

        for store in stores:
            addr_1 = store["address_1"]
            addr_2 = store["address_2"]
            addr_3 = store["address_3"]

            properties = {
                "name": store["name"],
                "ref": store["id"],
                "addr_full": re.sub(
                    " +", " ", " ".join(filter(None, [addr_1, addr_2, addr_3])).strip()
                ),
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postal_code"],
                "country": store["country_code"],
                "phone": store.get("phone_number"),
                "website": response.url,
                "lat": float(store["latitude"]),
                "lon": float(store["longitude"]),
                "extras": {
                    "store_type": store["type"],
                },
            }

            yield GeojsonPointItem(**properties)
