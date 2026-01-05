from copy import deepcopy

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class ManTruckAndBusSpider(scrapy.Spider):
    name = "man_truck_and_bus"
    start_urls = ["https://settlement.man.eu/settlement/public/mui/world.js?"]
    item_attributes = {"brand": "MAN", "brand_wikidata": "Q708667"}
    vehicle_ids = [0, 1, 2]
    # 0 - Truck
    # 1 - Bus
    # 2 - Van

    def parse(self, response: Response, **kwargs):
        for store in response.json():
            name_data = store[1]
            address_data = store[2]
            coordinates_data = store[3]
            phone_data = store[4]
            services = store[5]
            sales = store[6]
            item = Feature()
            item["ref"] = store[0]
            item["name"] = name_data[0] or name_data[1]
            item["phone"] = phone_data[0]
            item["street_address"] = address_data[0]
            item["postcode"] = address_data[1]
            item["city"] = address_data[2]
            item["country"] = address_data[3]
            if len(coordinates_data) == 2:
                item["lat"] = coordinates_data[1]
                item["lon"] = coordinates_data[0]
            if any(i in self.vehicle_ids for i in sales):
                shop_item = deepcopy(item)
                shop_item["ref"] = f"{item['ref']}-SHOP"
                apply_category(Categories.SHOP_TRUCK, shop_item)
                yield shop_item
            if any(i in self.vehicle_ids for i in services):
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-SERVICE"
                apply_category(Categories.SHOP_TRUCK_REPAIR, service_item)
                yield service_item
