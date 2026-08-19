from typing import Any

import scrapy
from scrapy.http import Response

from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosSGSpider(scrapy.Spider):
    name = "nandos_sg"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["nandos.com.sg"]
    start_urls = ["https://www.nandos.com.sg/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[contains(@class,"flex flex-col gap-3 ")]'):
            item = Feature()
            item["branch"] = item["ref"] = location.xpath("./h3/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            yield item
