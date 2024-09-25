from urllib.parse import urljoin

import scrapy

from locations.structured_data_spider import StructuredDataSpider


class BeaverbrooksGBSpider(StructuredDataSpider):
    name = "beaverbrooks_gb"
    item_attributes = {"brand": "Beaverbrooks", "brand_wikidata": "Q4878226"}
    start_urls = [
        "https://www.beaverbrooks.co.uk/stores",
    ]

    def parse(self, response):
        locations = response.xpath('//li[contains(@class, "stores-list__store  ")]/@data-store-link').getall()
        for location in locations:
            url = urljoin("https://www.beaverbrooks.co.uk", location)
            yield scrapy.Request(url=url, callback=self.parse_sd)
