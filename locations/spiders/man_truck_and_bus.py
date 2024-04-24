import scrapy

from locations.items import Feature


class ManTruckAndBusSpider(scrapy.Spider):
    name = "man_truck_and_bus"
    start_urls = ["https://settlement.man.eu/settlement/public/mui/world.js?"]

    item_attributes = {
        "brand": "MAN Truck & Bus",
        "brand_wikidata": "Q708667",
        "extras": {"shop": "truck"},
    }

    def parse(self, response, **kwargs):
        for store in response.json():
            name_data = store[1]
            address_data = store[2]
            coordinates_data = store[3]
            phone_data = store[4]
            name = name_data[0] or name_data[1]

            if len(coordinates_data) < 2:
                continue

            yield Feature(
                {
                    "ref": store[0],
                    "name": name,
                    "street_address": address_data[0],
                    "phone": phone_data[0],
                    "postcode": address_data[1],
                    "city": address_data[2],
                    "country": address_data[3],
                    "lat": coordinates_data[1],
                    "lon": coordinates_data[0],
                }
            )
