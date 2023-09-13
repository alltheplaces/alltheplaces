import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class MaverikSpider(scrapy.Spider):
    name = "maverik"
    item_attributes = {"brand": "Maverik", "brand_wikidata": "Q64149010"}
    allowed_domains = ["maverik.com"]
    requires_proxy = True

    def start_requests(self):
        yield scrapy.Request("https://gateway.maverik.com/ac-loc/location/all", callback=self.add_fuels)

    def add_fuels(self, response):
        yield scrapy.Request(
            "https://gateway.maverik.com/ac-loc/location/fuel/all",
            headers={"APP-ID": "PAYX"},
            meta=response.json(),
        )

    def parse(self, response):
        locations = response.meta["locations"]
        fuels = response.json()

        for location in locations:
            address = location["address"]
            fuel = next((f for f in fuels if f["storeCode"] == location["code"]), {})
            store_fuels = [f["fuelType"] for f in fuel.get("priceMatchDiscounts", [])]
            metadata = location.get("metadata", [{}])[0]

            if not ("longitude" in location and "latitude" in location):
                continue

            item = Feature(
                lon=location["longitude"],
                lat=location["latitude"],
                ref=location["code"],
                extras={"branch": location["name"]},
                street_address=address["address1"],
                city=address["city"],
                state=address["stateProvince"],
                postcode=address["postalCode"],
                country=address["country"],
                phone=address["phone"],
                opening_hours="24/7" if "12:00AM - 12:00AM" == location.get("hoursOfOperation") else None,
            )

            apply_category(Categories.FUEL_STATION, item)

            # "BTO" "Cinnabon" "ETHANOL_FREE" "Freeway/Highway" "Hi_Flow_La" "Pizza" "R_V__Dumps" "Tables_Chairs"
            # "grab&go"
            apply_yes_no(Extras.ATM, item, metadata.get("ATM"))
            apply_yes_no(Extras.COMPRESSED_AIR, item, metadata.get("Air_Machine"))
            apply_yes_no("hgv", item, metadata.get("Hi_Flow_La"))
            apply_yes_no(Fuel.HGV_DIESEL, item, metadata.get("Hi_Flow_La"))
            apply_yes_no("sells:lottery", item, metadata.get("Lottery"))
            apply_yes_no("rv", item, metadata.get("RV_Lanes"))

            # "Car DSL" "DEF" "Ethanol-Free" "Mid-High" "Mid-Low" "Premium" "Truck DSL" "Unleaded"
            apply_yes_no(Fuel.E15, item, "E15" in store_fuels)

            yield item
