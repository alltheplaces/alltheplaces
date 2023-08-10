import scrapy

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
            fuel = next((f for f in fuels if f["storeCode"] == location["code"]), None)
            metadata = location.get("metadata")

            if not ("longitude" in location and "latitude" in location):
                continue

            yield Feature(
                lon=location["longitude"],
                lat=location["latitude"],
                ref=location["code"],
                name=f"Maverick {location['name']}",
                street_address=address["address1"],
                city=address["city"],
                state=address["stateProvince"],
                postcode=address["postalCode"],
                country=address["country"],
                phone=address["phone"],
                opening_hours="24/7" if "12:00AM - 12:00AM" == location.get("hoursOfOperation") else None,
                extras={
                    "rv": metadata and any(m.get("RV_Lanes") for m in metadata) or None,
                    "hgv": metadata and any(m.get("Hi_Flow_La") for m in metadata) or None,
                    "fuel:HGV_diesel": metadata and any(m.get("Hi_Flow_La") for m in metadata),
                    "fuel:diesel": fuel and any(f["fuelType"] == "Diesel" for f in fuel["priceMatchDiscounts"]) or None,
                    "amenity:fuel": True,
                    # 'amenity:toilets': 'Restroom' in details or None,
                    # 'atm': 'ATM' in details,
                    # 'car_wash': 'Car Wash' in details,
                    # 'fuel:diesel': 'Diesel' in details or None,
                    # 'fuel:e85': 'E-85' in details or None,
                },
            )
