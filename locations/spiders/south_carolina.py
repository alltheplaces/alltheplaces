import json

import scrapy

from locations.items import Feature


class SouthCarolinaSpider(scrapy.Spider):
    download_delay = 0.2
    name = "south_carolina"
    allowed_domains = ["sc.gov"]
    start_urls = ("https://applications.sc.gov/PortalMapApi/api/Map/GetMapItemsByCategoryId/1,2,3,4,5,6,7",)
    item_attributes = {"brand_wikidata": "Q1456"}
    requires_proxy = True

    def parse(self, response):
        cat = (
            "State Park",
            "Library",
            "Department of Health and Human Resources",
            "Court House",
            "Department of Mental Health",
            "Department of Motor Vehicles",
            "SC Works",
        )
        data = json.loads(json.dumps(response.json()))

        for i in data:
            try:
                properties = {
                    "ref": i["Id"],
                    "name": i["Description"],
                    "extras": {
                        "category": (cat[int(i["CategoryId"]) - 1]),
                    },
                    "addr_full": i["Address"],
                    "postcode": i["Zipcode"],
                    "country": "US",
                    "phone": i["Telephone"],
                    "lat": float(i["Latitude"]),
                    "lon": -abs(float(i["Longitude"])),
                }

                yield Feature(**properties)

            except:
                pass
