import json
from io import BytesIO
from time import sleep
from zipfile import ZipFile

import scrapy

from locations.categories import Extras, Fuel, apply_yes_no
from locations.items import Feature


class SpeedwayUSSpider(scrapy.Spider):
    name = "speedway_us"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}
    allowed_domains = ["mobileapps.speedway.com"]
    requires_proxy = True

    def start_requests(self):
        # We make this request to start a session and store cookies that the actual request requires
        yield scrapy.Request("https://mobileapps.speedway.com/", callback=self.get_results)

    def get_results(self, response):
        self.logger.debug("Waiting 5 seconds to make make the session cookie stick...")
        sleep(5)
        yield scrapy.Request(
            "https://mobileapps.speedway.com/S3cur1ty/VServices/StoreService.svc/getallstores/321036B0-4359-4F4D-A01E-A8DDEE0EC2F7"
        )

    def parse(self, response):
        z = ZipFile(BytesIO(response.body))
        stores = json.loads(z.read("SpeedwayStores.json").decode("utf-8", "ignore").encode("utf-8"))

        for store in stores:
            amenities = [amenity["name"] for amenity in store["amenities"]]
            fuels = [fuel["description"] for fuel in store["fuelItems"]]

            item = Feature(
                lat=store["latitude"],
                lon=store["longitude"],
                name=store["brandName"],
                street_address=store["address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip"],
                country="US",
                opening_hours="24/7" if "Open 24 Hours" in amenities else None,
                phone=store["phoneNumber"],
                website=f"https://www.speedway.com/locations/store/{store['costCenterId']}",
                ref=store["costCenterId"],
            )

            apply_yes_no(Extras.ATM, item, "ATM" in amenities)
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in amenities)
            apply_yes_no(Fuel.PROPANE, item, "Propane" in amenities)
            apply_yes_no(Fuel.DIESEL, item, "DSL" in fuels)
            apply_yes_no(Fuel.E15, item, "E15" in fuels)
            apply_yes_no(Fuel.E20, item, "E20" in fuels)
            apply_yes_no(Fuel.E30, item, "E30" in fuels)
            apply_yes_no(Fuel.E85, item, "E85" in fuels)
            apply_yes_no(Fuel.OCTANE_87, item, "Unleaded" in fuels)
            apply_yes_no(Fuel.OCTANE_89, item, "Plus" in fuels)
            apply_yes_no(Fuel.OCTANE_90, item, "90" in fuels)
            apply_yes_no(Fuel.OCTANE_91, item, "91" in fuels)
            apply_yes_no(Fuel.OCTANE_93, item, "Premium" in fuels)
            apply_yes_no(Fuel.OCTANE_100, item, "Racing" in fuels)
            apply_yes_no("hgv", item, "Truck" in fuels)
            apply_yes_no(Fuel.HGV_DIESEL, item, ("Truck" in fuels or "Truck" in amenities))
            apply_yes_no(Fuel.OCTANE_87, item, "Unleaded" in fuels)

            yield item
