from urllib.parse import urljoin

import scrapy

from locations.structured_data_spider import StructuredDataSpider


class FHindsGBSpider(StructuredDataSpider):
    name = "f_hinds_gb"
    item_attributes = {"brand": "F Hinds", "brand_wikidata": "Q5423915"}
    start_urls = [
        "https://www.fhinds.co.uk/store-locator?view_all=true",
    ]

    def parse(self, response):
        locations = response.xpath('//*[@class="store-title"]//@href').getall()
        for location in locations:
            url = urljoin("https://www.fhinds.co.uk", location)
            yield scrapy.Request(url=url, callback=self.parse_sd)
