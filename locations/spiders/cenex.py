# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class CenexSpider(scrapy.Spider):
    name = "cenex"
    item_attributes = {"brand": "Cenex", "brand_wikidata": "Q5011381"}
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
            amenities = "|".join([a["Name"] for a in store["Amenities"]])

            yield GeojsonPointItem(
                lon=store["Long"],
                lat=store["Lat"],
                ref=store["LocationId"],
                name=store["Name"],
                addr_full=" ".join([store["Address1"], store["Address2"]]).strip(),
                city=store["City"],
                state=store["State"],
                postcode=store["Zip"],
                country="US",
                phone=store["Phone"],
                website=store["WebsiteUrl"],
                opening_hours="24/7" if "24-Hour" in amenities else None,
                extras={
                    "amenity:fuel": True,
                    "atm": "ATM" in amenities,
                    "car_wash": "Car Wash" in amenities,
                    "fuel:biodiesel": "Biodiesel" in amenities or None,
                    "fuel:diesel": "Diesel" in amenities or None,
                    "fuel:e85": "Flex Fuels" in amenities or None,
                    "fuel:HGV_diesel": "Truck Stop" in amenities or None,
                    "fuel:propane": "Propane" in amenities or None,
                    "hgv": "Truck Stop" in amenities or None,
                    "shop": "convenience" if "Convenience Store" in amenities else None,
                },
            )
