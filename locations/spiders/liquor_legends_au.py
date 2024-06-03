from json import loads

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class LiquorLegendsAUSpider(Spider):
    name = "liquor_legends_au"
    item_attributes = {
        "brand": "Liquor Legends",
        "brand_wikidata": "Q126175687",
        "extras": Categories.SHOP_ALCOHOL.value,
    }
    allowed_domains = ["rewardsapi.liquorlegends.com.au"]
    start_urls = ["https://rewardsapi.liquorlegends.com.au/api/v1/venue/geo-json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            location_details = loads(location["properties"]["location_data"])["store_details"]

            properties = {
                "ref": str(location_details["outlet_id"]),
                "name": location_details["store_name"],
                "geometry": location["geometry"],
                "street_address": location_details["location_details"]["street_address"],
                "city": location_details["location_details"]["suburb"],
                "state": location_details["location_details"]["state"],
                "postcode": location_details["location_details"]["postcode"],
                "phone": location_details["contact_details"]["phone"],
                "email": location_details["contact_details"]["email"],
                "opening_hours": OpeningHours(),
            }

            if properties["name"].startswith("Liquor Legends "):
                properties["branch"] = properties["name"].replace("Liquor Legends ", "")

            hours_json = loads(location["properties"]["opening_hours"])
            for day_name in DAYS_FULL:
                if day_hours := hours_json.get(day_name):
                    properties["opening_hours"].add_range(day_name, day_hours["open"], day_hours["close"], "%I:%M%p")

            yield Feature(**properties)
