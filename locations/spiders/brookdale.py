# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

URL = "https://www.brookdale.com/bin/brookdale/community-search?care_type_category=resident&loc=&finrpt=&state="

US_STATES = (
    "AL",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
)


class TemplateSpider(scrapy.Spider):
    name = "brookdale"
    item_attributes = {"brand": "Brookdale"}
    allowed_domains = ["www.brookdale.com"]

    def start_requests(self):
        for state in US_STATES:
            url = "".join([URL, state])
            yield scrapy.Request(url, callback=self.parse_info)

    def parse_info(self, response):

        data = response.json()

        for row in data:

            properties = {
                "ref": row["community_id"],
                "name": row["name"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "addr_full": row["address1"],
                "city": row["city"],
                "state": row["state"],
                "country": row["country_code"],
                "postcode": row["zip_postal_code"],
                "website": row["website"],
                "phone": row["contact_center_phone"],
            }

            yield GeojsonPointItem(**properties)
