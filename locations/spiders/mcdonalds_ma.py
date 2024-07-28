import re

import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsMASpider(scrapy.Spider):
    name = "mcdonalds_ma"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.ma"]
    start_urls = ("http://www.mcdonalds.ma/nos-restaurants/r%C3%A9seau-maroc",)

    def parse_address(self, data):
        address = ""
        city = ""
        matches = re.finditer(r"([\w|\s|\,]{1,}) <br>", data)

        for match_num, match in enumerate(matches):
            if match_num == 0:
                address = match.groups()[0].strip()
            elif match_num == 1:
                city = match.groups()[0].strip()

        return address, city

    def parse_phone(self, data):
        match = re.search(r"Tél : (.[\d|\s]{1,})", data)
        if not match:
            return ""
        return match.groups()[0].strip()

    def parse(self, response):
        stores = response.xpath('//div[@class="cont_restau_infos"]')
        index = 0
        for store in stores:
            name = store.xpath('.//span[@class="restauName"]/text()').extract_first().strip()
            data = store.extract().strip()
            address, city = self.parse_address(data)
            phone = self.parse_phone(data)

            properties = {
                "city": city,
                "ref": index,
                "addr_full": address,
                "phone": phone,
                "name": name,
            }
            index = index + 1
            yield Feature(**properties)
