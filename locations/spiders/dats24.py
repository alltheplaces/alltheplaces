import json

import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature

fuel_map = {
    13: Fuel.CNG,
    14: Fuel.OCTANE_95,
    15: Fuel.OCTANE_98,
    16: Fuel.DIESEL,
    58: Fuel.ADBLUE,
}


class Dats24BESpider(scrapy.Spider):
    name = "dats24_be"
    item_attributes = {"brand": "DATS 24", "brand_wikidata": "Q15725576"}
    start_urls = ["https://customer.dats24.be/wps/portal/datscustomer/fr/b2c/locator"]

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@class="locatorMapData"]/text()').get())
        for store in data.get("stores"):
            item = Feature(
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
            services = store.get("featureIds")
            for key, value in fuel_map.items():
                if key in services:
                    apply_yes_no(value, item, True)

            apply_category(Categories.FUEL_STATION, item)
            yield item
