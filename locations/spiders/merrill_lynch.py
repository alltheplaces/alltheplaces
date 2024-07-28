import json

import scrapy

from locations.items import Feature


class MerrillLynchSpider(scrapy.Spider):
    name = "merrill_lynch"
    item_attributes = {"brand": "Merrill Lynch", "brand_wikidata": "Q334122"}
    allowed_domains = ["ml.com"]
    start_urls = ("https://fa.ml.com/",)

    def parse_branch(self, response):
        data = response.json()

        for location in data["Results"]:
            properties = {
                "ref": location["UniqueId"],
                "name": location["Company"],
                "street_address": location["Address1"].strip(),
                "city": location["City"],
                "state": location["Region"],
                "country": location["Country"],
                "postcode": location["PostalCode"],
                "lat": float(location["GeoLat"]),
                "lon": float(location["GeoLon"]),
                "website": location["XmlData"]["parameters"].get("Url"),
                "extras": {"unit": location.get("Address2") or None},
            }

            yield Feature(**properties)

    def parse(self, response):
        states = response.xpath('//section[@class="state-view"]//li/a/@data-state-abbrev').extract()

        for state in states:
            url = "https://fa.ml.com/locator/api/InternalSearch"
            payload = {
                "Locator": "MER-WM-Offices",
                "Region": state,
                "Company": None,
                "ProfileTypes": "Branch",
                "DoFuzzyNameSearch": 0,
                "SearchRadius": 100,
            }
            yield scrapy.Request(
                url,
                method="POST",
                body=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                callback=self.parse_branch,
            )
