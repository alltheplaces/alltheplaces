import re

import scrapy

from locations.items import Feature
from locations.spiders.subway import SubwaySpider
from locations.spiders.vapestore_gb import clean_address


class SubwayTHSpider(scrapy.Spider):
    name = "subway_th"
    item_attributes = SubwaySpider.item_attributes
    start_urls = ["https://www.subway.co.th/en/layouts/page_restaurant_locator.html"]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.xpath('//*[@class="restaurant_locator"]//ul/li'):
            item = Feature()
            item["name"] = location.xpath('.//a[contains(@href,"Map")]/text()').get()
            address = clean_address(location.xpath("./text()").getall()).replace("\n", "")
            result = re.split(r"Tel[./]?|Contact No[./]?", address.title(), maxsplit=1)
            item["addr_full"], item["phone"] = result if len(result) == 2 else [address, None]

            # separate phone appended to address without Tel like key word
            if match := re.search(r"(.+?)([-\d]{10,})", item["addr_full"]):
                item["addr_full"], item["phone"] = match.groups()

            item["addr_full"] = re.sub(r"\s+", " ", clean_address(item["addr_full"]))
            if item["phone"]:
                if "Fax" in item["phone"]:
                    item["phone"], item["extras"]["fax"] = item["phone"].split("Fax")
                item["phone"] = item["phone"].replace(",", ";")
            yield item
