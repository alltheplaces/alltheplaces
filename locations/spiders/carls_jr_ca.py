import re

import scrapy

from locations.items import Feature
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrCASpider(scrapy.Spider):
    name = "carls_jr_ca"
    item_attributes = CarlsJrUSSpider.item_attributes
    start_urls = ["https://www.carlsjr.ca/locations"]

    def parse(self, response, **kwargs):
        for location in response.xpath("//div[@id][@data-testid]//p"):
            location_text = location.xpath(".//span//text()").get(default="").strip()
            if re.match(r"\d+", location_text) or "Airport" in location_text.title():
                item = Feature()
                item["ref"] = item["street_address"] = location_text
                item["phone"] = location.xpath('./following-sibling::p//span[contains(text(),"PH:")]/text()').get()
                hours = location.xpath('./following-sibling::p//span[contains(text(),"HOURS:")]/text()').get()
                if not hours:  # not a valid location
                    continue
                # opening hours ignored because of inconsistent data
                item["website"] = response.url
                yield item
