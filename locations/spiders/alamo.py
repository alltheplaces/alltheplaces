import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class AlamoSpider(scrapy.Spider):
    name = "alamo"
    item_attributes = {"brand": "Alamo", "brand_wikidata": "Q1429287"}
    allowed_domains = ["alamo.com"]
    start_urls = ["https://prd.location.enterprise.com/enterprise-sls/search/location/alamo/web/all?dto=true"]

    def parse(self, response):
        for loc in response.json():
            properties = {
                "branch": loc["name"],
                "phone": "; ".join([p["phone_number"] for p in loc["phones"]]),
                "street_address": clean_address(loc["address"]["street_addresses"]),
                "city": loc["address"].get("city"),
                "state": loc["address"]["country_subdivision_code"],
                "postcode": loc["address"]["postal"],
                "country": loc["address"].get("country_code"),
                "lat": float(loc["gps"]["latitude"]),
                "lon": float(loc["gps"]["longitude"]),
                "ref": loc["id"],
            }

            yield Feature(**properties)
