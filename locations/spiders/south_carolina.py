import json

import scrapy

from locations.items import Feature


class SouthCarolinaSpider(scrapy.Spider):
    download_delay = 0.2
    name = "south_carolina"
    allowed_domains = ["sc.gov"]
    start_urls = ("https://applications.sc.gov/PortalMapApi/api/Map/GetMapItemsByCategoryId/1,2,3,4,5,6,7",)
    item_attributes = {"brand_wikidata": "Q1456"}

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
                item = DictParser.parse(i)
                item["lon"] = -abs(float(i["Longitude"]))
                item["country"] = "US"
                item["name"] = i["Description"]

                category_mapping = cat[int(i["CategoryId"]) - 1]

                if category_mapping == "Libary":
                    apply_category(Category.LIBRARY, item)
                elif category_mapping == "Court House":
                    apply_category({"amenity": "courthouse"}, item)
                else:
                    item["extras"] = {
                        "category": category_mapping
                    }

                yield item

            except:
                pass
