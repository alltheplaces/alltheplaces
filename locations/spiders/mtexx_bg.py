from scrapy import Spider

from locations.items import Feature

import re

class MtexxBGSpider(Spider):
    name = "mtexx_bg"
    item_attributes = {"brand": "M-texx", "brand_wikidata": "Q122947768"}
    allowed_domains = ["www.m-texx.com"]
    start_urls = ["https://m-texx.com/локации"]

    def parse(self, response):
        for locations in response.xpath("//div[@data-ux='ContentText']"):
            for location in locations.xpath("//li"):
                text = location.get()
                coords = re.findall(r'(\d+\.\d+,\ \d+\.\d+|\d+°\d+\'\d+\.\d+"[NS]\s\d+°\d+\'\d+\.\d+"[EW])', text)
                properties = {
                    "name": text.rsplit("-")[0],
                    "lat": coords[0],
                    "lon": coords[1],
                }
                yield Feature(**properties)
