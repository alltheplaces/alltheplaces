from scrapy import Request, Spider

from locations.categories import Categories, Extras, Fuel, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class Dats24BESpider(Spider):
    name = "dats_24_be"
    item_attributes = {"brand": "DATS 24", "brand_wikidata": "Q15725576", "extras": Categories.FUEL_STATION.value}
    start_urls = ["https://dats24.be/api/service_point_locator"]
    allowed_domains = ["dats24.be"]

    def start_requests(self):
        query = '{"latitude":0,"longitude":0,"searchRadius":1000000000,"filterCriteria":{"serviceDeliveryPointType":["FUEL"],"serviceDeliveryPointAvailability":[],"chargingConnectorType":[],"chargingConnectorPowerType":[],"chargingLocationOperatorName":["ALL"],"fuelProductType":[]}}'
        yield Request(
            url=self.start_urls[0],
            method="POST",
            body=query,
            headers={"Content-Type": "text/plain;charset=UTF-8"},
            callback=self.parse_locations_list,
        )

    def parse_locations_list(self, response):
        for location in response.json()["serviceDeliveryPoints"]:
            item = Feature()
            item["ref"] = location["fuelStation"]["id"]
            item["name"] = location["fuelStation"]["name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            query = '{"deliveryPointId":' + str(location["fuelStation"]["id"]) + ',"deliveryPointType":"FUEL"}'
            yield Request(
                url="https://dats24.be/api/service_point_details",
                method="POST",
                body=query,
                headers={"Content-Type": "text/plain;charset=UTF-8"},
                meta={"item": item},
                callback=self.parse_location_details,
            )

    def parse_location_details(self, response):
        item = response.meta["item"]
        location_details = response.json()["serviceDeliveryPoint"]
        location_details["street_address"] = location_details.pop("street", None)
        item2 = DictParser.parse(location_details)
        item2["ref"] = item["ref"]
        item2["name"] = item["name"]
        item2["lat"] = item["lat"]
        item2["lon"] = item["lon"]
        item2["addr_full"] = location_details.pop("address", None)
        product_codes = [product["code"] for product in location_details["fuelStation"]["products"]]
        apply_yes_no(Fuel.E10, item2, "U" in product_codes, False)
        apply_yes_no(Fuel.OCTANE_98, item2, "P" in product_codes, False)
        apply_yes_no(Fuel.DIESEL, item2, "D" in product_codes, False)
        apply_yes_no(Fuel.CNG, item2, "C" in product_codes, False)
        apply_yes_no(Fuel.ADBLUE, item2, "A" in product_codes, False)
        apply_yes_no(Extras.COMPRESSED_AIR, item2, "B" in product_codes, False)
        yield item2
