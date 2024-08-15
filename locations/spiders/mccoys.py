from urllib.parse import urljoin

import scrapy

from locations.structured_data_spider import StructuredDataSpider


class MccoysSpider(StructuredDataSpider):
    name = "mccoys"
    item_attributes = {"brand": "McCoy's Building Supply", "brand_wikidata": "Q27877295"}
    start_urls = ["https://www.mccoys.com/stores"]
    time_format = "%I%p"

    def parse(self, response):
        locations = response.xpath('//*[@class="btn btn-block btn-outline-secondary"]//@href').getall()
        for location in locations:
            url = urljoin("https://www.mccoys.com", location)
            yield scrapy.Request(url=url, callback=self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHoursSpecification"] = ld_data.pop("OpeningHoursSpecification", None)
