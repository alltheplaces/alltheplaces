import scrapy
from locations.items import GeojsonPointItem


class ElPolloLocoSpider(scrapy.Spider):
    name = "elpolloloco"
    item_attributes = {"brand": "El Pollo Loco", "brand_wikidata": "Q2353849"}
    allowed_domains = ["www.elpolloloco.com"]
    start_urls = ("https://www.elpolloloco.com/locations/locations_json",)

    def start_requests(self):
        template = "https://www.elpolloloco.com/locations/locations_json"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        store_data = response.json()
        for store in store_data:
            try:
                properties = {
                    "ref": store[0],
                    "name": store[12],
                    "addr_full": store[1],
                    "city": store[3],
                    "state": store[4],
                    "postcode": store[5],
                    "phone": store[6],
                    "lat": float(store[8]),
                    "lon": float(store[9]),
                    "website": response.url,
                }
                yield GeojsonPointItem(**properties)

            except ValueError:
                continue
