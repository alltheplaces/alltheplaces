from typing import Any

import scrapy
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class NationalSpider(scrapy.Spider):
    name = "national"
    item_attributes = {"brand": "National", "brand_wikidata": "Q1424142"}
    start_urls = ["https://prd.location.enterprise.com/enterprise-sls/search/location/national/web/all?cor=US&dto=true"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        loc_data = response.json()

        for loc in loc_data:
            if loc["brand"] != "NATIONAL":
                self.logger.error("Unexpected brand: {}".format(loc["brand"]))
            properties = {
                "branch": loc["name"],
                "phone": loc["phones"][0]["phone_number"],
                "street_address": clean_address(loc["address"]["street_addresses"]),
                "city": loc["address"]["city"],
                "state": loc["address"]["country_subdivision_code"],
                "postcode": loc["address"]["postal"],
                "country": loc["address"]["country_code"],
                "lat": float(loc["gps"]["latitude"]),
                "lon": float(loc["gps"]["longitude"]),
                "ref": loc["id"],
            }

            yield Feature(**properties)
