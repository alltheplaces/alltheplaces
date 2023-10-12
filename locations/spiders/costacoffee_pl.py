import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class CostaCoffeePLSpider(scrapy.Spider):
    name = "costacoffee_pl"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["api.costacoffee.pl"]
    start_urls = ["https://api.costacoffee.pl/api/storelocator/list"]

    def parse(self, response):
        data = response.json()
        for store in data:
            properties = {
                "name": store["name"],
                "street_address": store["address"],
                "city": store["city"],
                "postcode": store["postCode"],
                "country": "PL",
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["address"],
                            store["city"],
                            store["postCode"],
                            "Poland",
                        ),
                    ),
                ),
                "lat": store["gpsY"],
                "lon": store["gpsX"],
                "extras": {
                    "store_type": store["type"],
                    "delivery": "yes" if store["deliveryAvailable"] else "no",
                },
            }

            # No ref in upstream data, so we just want something as unique as possible
            properties["ref"] = "|".join(
                (
                    properties["lat"],
                    properties["lon"],
                    properties["name"],
                    properties["addr_full"],
                )
            )

            apply_category(Categories.CAFE, properties)

            yield Feature(**properties)
