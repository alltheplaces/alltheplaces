import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CenexSpider(scrapy.Spider):
    name = "cenex"
    item_attributes = {"brand": "Cenex", "brand_wikidata": "Q62127191"}
    allowed_domains = ["www.cenex.com"]

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://www.cenex.com/Common/Services/InteractiveMap.svc/GetLocations",
            method="POST",
            data={
                "SearchRequest": {
                    "Metadata": {"MapId": "", "Categories": []},
                    "Query": {
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
                },
                "MapItemId": "40381d43-1c05-43e0-8477-78737b9974df",
                "AllOrganizationIds": [
                    "b4ed9d2c-cc3b-4ce0-b642-79d75eac11fa",
                    "cb27078e-9b6a-4f4d-ac81-eb1d163a5ff6",
                    "68be9e56-ff49-4724-baf0-90fc833fb459",
                    "28e93e82-edfa-418e-90aa-7ded057a0c68",
                ],
                "ServiceUrl": "https://locatorservice.chsinc.ds/api/search",
            },
        )

    def parse(self, response):
        result = response.json()

        for store in result["SearchResponse"]["Locations"]:
            amenities = [a["Name"] for a in store["Amenities"]]
            item = Feature(
                lon=store["Long"],
                lat=store["Lat"],
                ref=store["LocationId"],
                name=store["Name"],
                street_address=merge_address_lines([store["Address1"], store["Address2"]]),
                city=store["City"],
                state=store["State"],
                postcode=store["Zip"],
                country="US",
                phone=store["Phone"],
                website=store["WebsiteUrl"],
                opening_hours="24/7" if "24-Hour Fueling" in amenities else None,
            )

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.ATM, item, "ATM" in amenities)
            apply_yes_no(Extras.COMPRESSED_AIR, item, "Air" in amenities)
            apply_yes_no(Fuel.BIODIESEL, item, "Biodiesel" in amenities)
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in amenities)
            # "Cenex® Lubricants"
            apply_yes_no(Fuel.DIESEL, item, "Cenex® Premium Diesel Fuel" in amenities)
            apply_yes_no("shop=yes", item, "Convenience Store" in amenities)
            # "DEF Available"
            apply_yes_no(Fuel.DIESEL, item, "Diesel Fuel" in amenities)
            apply_yes_no(Fuel.E85, item, "Flex Fuels" in amenities)
            # "Made Fresh Foods"
            # "No Inside Services"
            apply_yes_no(Fuel.PROPANE, item, "Propane Cylinder Filling or Exchange" in amenities)
            apply_yes_no("food=yes", item, "Restaurant" in amenities)
            apply_yes_no("hgv", item, "Truck Stop" in amenities)
            apply_yes_no(Fuel.HGV_DIESEL, item, "Truck Stop" in amenities)
            apply_yes_no(Extras.WIFI, item, "Wi-Fi" in amenities)

            yield item
