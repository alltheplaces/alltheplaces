import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CenexSpider(scrapy.Spider):
    name = "cenex"
    item_attributes = {"brand": "Cenex", "brand_wikidata": "Q62127191"}

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://www.cenex.com/getlocationsearch",
            method="POST",
            data={
                "SearchLat": 0,
                "SearchLong": 0,
                "LocationTypes": [1, 16, 15],
                "Amenities": [],
                "Organizations": ["28e93e82-edfa-418e-90aa-7ded057a0c68"],
                "NELat": 90,
                "NELong": 180,
                "SWLat": -90,
                "SWLong": -180,
            },
        )

    def parse(self, response):
        for store in response.json()["Locations"]:
            amenities = [a["Name"] for a in store["Amenities"]]
            item = Feature(
                lon=store["Long"],
                lat=store["Lat"],
                ref=store["Id"],
                name=store["Name"],
                addr_full=store["Address"],
                country="US",
                phone=store["Phone"],
                opening_hours="24/7" if "24-hour fueling" in amenities else None,
            )

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.ATM, item, "ATM" in amenities)
            apply_yes_no(Extras.COMPRESSED_AIR, item, "Air" in amenities)
            apply_yes_no(Fuel.BIODIESEL, item, "Biodiesel" in amenities)
            apply_yes_no(Extras.CAR_WASH, item, "Car wash" in amenities)
            # "Cenex® Lubricants"
            apply_yes_no(Fuel.DIESEL, item, "Cenex® premium diesel fuel" in amenities)
            apply_yes_no("shop=yes", item, "Convenience store" in amenities)
            # "DEF Available"
            apply_yes_no(Fuel.DIESEL, item, "Diesel fuel" in amenities)
            apply_yes_no(Fuel.E85, item, "Flex fuels" in amenities)
            # "Made Fresh Foods"
            # "No Inside Services"
            apply_yes_no(Fuel.PROPANE, item, "Propane cylinder filling or exchange" in amenities)
            apply_yes_no("food=yes", item, "Restaurant" in amenities)
            apply_yes_no("hgv", item, "Truck stop" in amenities)
            apply_yes_no(Fuel.HGV_DIESEL, item, "Truck stop" in amenities)
            apply_yes_no(Extras.WIFI, item, "Wi-Fi" in amenities)

            yield item
