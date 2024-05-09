import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.pipelines.address_clean_up import clean_address


class PNCSpider(scrapy.Spider):
    name = "pnc"
    item_attributes = {"brand": "PNC Bank", "brand_wikidata": "Q38928", "country": "US"}
    allowed_domains = ["www.pnc.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for lat, lon in point_locations("us_centroids_100mile_radius.csv"):
            yield scrapy.Request(
                f"https://apps.pnc.com/locator-api/locator/api/v2/location/?latitude={lat}&longitude={lon}&radius=100&radiusUnits=mi&branchesOpenNow=false"
            )

    def parse(self, response):
        for branch in response.json()["locations"]:
            branch["ref"] = branch.pop("locationId")
            branch["name"] = branch.pop("locationName")
            branch["street_address"] = clean_address([branch["address"].pop("address1"), branch["address"].pop("address2")]),
            branch["location"] = {
                "latitude": branch["address"].pop("latitude"),
                "longitude": branch["address"].pop("longitude"),
            }
            item = DictParser.parse(branch)
            if "BRANCH" in branch["locationType"]["locationTypeDesc"]:
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)

            yield item
