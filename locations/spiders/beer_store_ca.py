import datetime

import scrapy
from scrapy.http import JsonRequest

from locations.items import Feature


class BeerStoreCASpider(scrapy.Spider):
    name = "beer_store_ca"
    item_attributes = {"brand": "The Beer Store", "brand_wikidata": "Q16243674"}
    start_urls = ["https://www.thebeerstore.ca/api/store"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                data={
                    "currentDate": datetime.date.today().isoformat(),
                    "lat": "44.9064",
                    "lang": "-93.2406",
                    "take": 6,
                    "skip": 0,
                },
            )

    def parse(self, response):
        results = response.json()
        features = results["data"]["items"]
        for data in features:
            properties = {
                "ref": data["id"],
                "lon": data["longitude"],
                "lat": data["latitude"],
                "branch": data["locationName"],
                "housenumber": data["streetNo"],
                "street": data["street"],
                "city": data["city"],
                "state": data["province"],
                "postcode": data["postalCode"],
                "country": data["country"],
                "phone": data["phone"],
            }

            yield Feature(**properties)
