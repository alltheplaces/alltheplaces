# -*- coding: utf-8 -*-
import scrapy
import json
from zipfile import ZipFile
from io import BytesIO
from time import sleep

from locations.items import GeojsonPointItem


class SpeedwaySpider(scrapy.Spider):
    name = "speedway"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}
    item_attributes = {"brand": "Speedway"}
    allowed_domains = ["mobileapps.speedway.com"]

    def start_requests(self):
        # We make this request to start a session and store cookies that the actual request requires
        yield scrapy.Request(
            "https://mobileapps.speedway.com/", callback=self.get_results
        )

    def get_results(self, response):
        self.logger.debug("Waiting 5 seconds to make make the session cookie stick...")
        sleep(5)
        yield scrapy.Request(
            "https://mobileapps.speedway.com/S3cur1ty/VServices/StoreService.svc/getallstores/321036B0-4359-4F4D-A01E-A8DDEE0EC2F7"
        )

    def parse(self, response):
        z = ZipFile(BytesIO(response.body))
        stores = json.loads(
            z.read("SpeedwayStores.json").decode("utf-8", "ignore").encode("utf-8")
        )

        for store in stores:
            amenities = store["amenities"]
            fuels = store["fuelItems"]

            yield GeojsonPointItem(
                lat=store["latitude"],
                lon=store["longitude"],
                name=store["brandName"],
                addr_full=store["address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip"],
                country="US",
                opening_hours="24/7"
                if any("Open 24 Hours" == a["name"] for a in amenities)
                else None,
                phone=store["phoneNumber"],
                website=f"https://www.speedway.com/locations/store/{store['costCenterId']}",
                ref=store["costCenterId"],
                extras={
                    "amenity:fuel": True,
                    "atm": any("ATM" == a["name"] for a in amenities),
                    "car_wash": any("Car Wash" == a["name"] for a in amenities),
                    "fuel:diesel": any("DSL" in f["description"] for f in fuels)
                    or None,
                    "fuel:e15": any("E15" == f["description"] for f in fuels) or None,
                    "fuel:e20": any("E20" == f["description"] for f in fuels) or None,
                    "fuel:e30": any("E30" == f["description"] for f in fuels) or None,
                    "fuel:e85": any("E85" == f["description"] for f in fuels) or None,
                    "fuel:HGV_diesel": any("Truck" in f["description"] for f in fuels)
                    or any("Truck" in a["name"] for a in amenities)
                    or None,
                    "fuel:octane_100": any("Racing" == f["description"] for f in fuels)
                    or None,
                    "fuel:octane_87": any("Unleaded" == f["description"] for f in fuels)
                    or None,
                    "fuel:octane_89": any("Plus" == f["description"] for f in fuels)
                    or None,
                    "fuel:octane_90": any("90" in f["description"] for f in fuels)
                    or None,
                    "fuel:octane_90": any("91" in f["description"] for f in fuels)
                    or None,
                    "fuel:octane_93": any("Premium" == f["description"] for f in fuels)
                    or None,
                    "fuel:propane": any("Propane" in a["name"] for a in amenities)
                    or None,
                    "hgv": any("Truck" in f["description"] for f in fuels) or None,
                },
            )
