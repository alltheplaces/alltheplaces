import json

import scrapy

from locations.items import Feature


class BjRestaurantSpider(scrapy.Spider):
    name = "bj_restaurant"
    item_attributes = {
        "brand": "BJ's Restaurant & Brewery",
        "brand_wikidata": "Q4835755",
    }
    allowed_domains = ["www.bjsrestaurants.com"]
    start_urls = ("https://www.bjsrestaurants.com/sitemap",)

    def extract_location_url(self, response):
        return response.xpath('//a[contains(@href, "locations")]/@href').extract()

    def parse_state(self, response):
        # Iterate over locations in each state
        for url in self.extract_location_url(response):
            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        # Store data is in two locations.
        # 1. <script type="application/ld+json">
        # 2. A data-location attribute
        # Some data exists in both locations

        schema_string = response.xpath('//*/script[@type="application/ld+json"]/text()').extract_first().strip(";\n")
        schema_dict = json.loads(schema_string)
        data_location_string = response.xpath("//@data-location").extract_first()
        data_location_dict = json.loads(data_location_string)
        return Feature(
            ref=data_location_dict["id"],
            lat=data_location_dict["latitude"],
            lon=data_location_dict["longitude"],
            name=schema_dict["name"],
            addr_full=schema_dict["address"]["streetAddress"],
            city=schema_dict["address"]["addressLocality"],
            state=schema_dict["address"]["addressRegion"],
            postcode=schema_dict["address"]["postalCode"],
            phone=schema_dict["telephone"],
            website=schema_dict["url"],
            opening_hours=self.parse_store_hours(schema_dict),
        )

    def parse_store_hours(self, store_dict):
        return ";".join(store_dict["openingHours"])

    def parse(self, response):
        # Iterate over all the state location pages
        for url in self.extract_location_url(response):
            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_state,
            )
