import json

import scrapy

from locations.items import Feature


class Dats24BESpider(scrapy.Spider):
    name = "dats24_be"
    item_attributes = {"brand": "DATS 24", "brand_wikidata": "Q15725576"}
    start_urls = ["https://customer.dats24.be/wps/portal/datscustomer/fr/b2c/locator"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@class="locatorMapData"]/text()').get())
        for store in data.get("stores"):
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "addr_full": " ".join(
                        filter(
                            None,
                            [store.get("houseNumber"), store.get("street"), store.get("city"), store.get("postalCode")],
                        )
                    ),
                    "street_address": " ".join(
                        filter(
                            None,
                            [store.get("houseNumber"), store.get("street")],
                        )
                    ),
                    "street": store.get("street"),
                    "postcode": store.get("postalCode"),
                    "city": store.get("city"),
                    "housenumber": store.get("houseNumber"),
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                }
            )
