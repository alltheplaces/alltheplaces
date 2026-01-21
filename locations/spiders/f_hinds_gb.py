from typing import Iterable
from urllib.parse import urljoin

import scrapy
from scrapy.http import TextResponse

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FHindsGBSpider(StructuredDataSpider):
    name = "f_hinds_gb"
    item_attributes = {"brand": "F.Hinds", "brand_wikidata": "Q5423915"}
    start_urls = [
        "https://www.fhinds.co.uk/store-locator?view_all=true",
    ]

    def parse(self, response):
        locations = response.xpath('//*[@class="store-title"]//@href').getall()
        for location in locations:
            url = urljoin("https://www.fhinds.co.uk", location)
            yield scrapy.Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("F.Hinds the Jewellers, ","")
        yield item
