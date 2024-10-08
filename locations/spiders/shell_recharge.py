import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class ShellRechargeSpider(scrapy.Spider):
    name = "shell_recharge"
    item_attributes = {"brand": "Shell Recharge", "brand_wikidata": "Q105883058"}

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            url="https://sky.shellrecharge.com/greenlots/coreapi/v3/sites/map-search",
            data={
                "latitude": 42.5,
                "longitude": -96.4,
                "radius": 3200,
                "limit": 100000,
                "offset": 0,
                "searchKey": "",
                "recentSearchText": "",
                "clearAllFilter": False,
                "connectors": [],
                "mappedCpos": ["GRL"],
                "comingSoon": False,
                "status": [],
                "excludePricing": True,
            },
        )

    def parse(self, response):
        for row in response.json()["data"]:
            properties = {
                "ref": row["id"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "name": row["name"],
                "street_address": row["address"],
                "city": row["city"],
                "state": row["stateCode"],
                "postcode": row["zipCode"],
                "country": row["country"],
            }

            apply_category(Categories.CHARGING_STATION, properties)

            yield Feature(**properties)
