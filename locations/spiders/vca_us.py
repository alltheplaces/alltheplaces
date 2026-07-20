from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class VcaUSSpider(scrapy.Spider):
    name = "vca_us"
    item_attributes = {"brand_wikidata": "Q7906620"}
    allowed_domains = ["vcahospitals.com"]
    start_urls = ["https://vcahospitals.com/find-a-hospital/location-directory"]
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 1}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath('//span[@class="location-accordion__location-name"]/a/@href').getall():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        ld_item = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        ld_item["openingHours"] = ld_item.pop("openingHours")[0].split(", ")

        item = LinkedDataParser.parse_ld(ld_item)
        item["branch"] = item.pop("name").strip("'").removeprefix("VCA ")
        item["lat"] = item.pop("lat")[:-1]
        item["lon"] = item.pop("lon")[:-1]
        item["ref"] = item["website"] = response.url

        apply_category(Categories.VETERINARY, item)
        yield item
