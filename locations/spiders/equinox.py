import json

import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class EquinoxSpider(scrapy.Spider):
    name = "equinox"
    item_attributes = {"brand": "Equinox Fitness", "brand_wikidata": "Q5384535"}
    allowed_domains = ["cdn.contentful.com"]
    start_url = "https://cdn.contentful.com/spaces/drib7o8rcbyf/environments/master/entries?content_type=club&include=3"
    user_agent = BROWSER_DEFAULT

    headers = {
        "Authorization": "Bearer jQC0m25d6MdSBGuBMFANzxpuWt5O_sdQOIYfLpqxcAI",
        "X-Contentful-User-Agent": "sdk contentful.js/0.0.0-determined-by-semantic-release; platform browser; os Windows;",
        "Origin": "https://www.equinox.com",
    }

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse, headers=self.headers, meta={"skip": 0})

    def parse(self, response):
        data = json.loads(response.text)
        for item in data["items"]:
            fields = item["fields"]
            yield Feature(
                name=fields["name"],
                street_address=fields["address"],
                city=fields["city"],
                state=fields["state"],
                postcode=fields["zip"],
                country=fields["country"],
                phone=fields["phoneNumber"],
                ref=fields["facilityId"],
                website=response.urljoin(fields["clubDetailPageURL"]),
            )
        records_read = data["skip"] + data["limit"]
        if records_read < data["total"]:
            yield scrapy.Request(
                f"{self.start_url}&skip={records_read}",
                callback=self.parse,
                headers=self.headers,
            )
