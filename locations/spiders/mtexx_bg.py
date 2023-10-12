import re

from scrapy import Spider

from locations.items import Feature


class MtexxBGSpider(Spider):
    name = "mtexx_bg"
    item_attributes = {"brand": "M-texx", "brand_wikidata": "Q122947768"}
    allowed_domains = ["www.m-texx.com"]
    start_urls = ["https://m-texx.com/локации"]

    def parse(self, response):
        for locations in response.xpath("//div[@data-ux='ContentText']"):
            for location in locations.xpath(".//li/text()"):
                text = location.get()
                data = re.search(
                    r'^(.+?)(\d+\.\d+|\d+°\d+\'\d+\.\d+"[NS])[\s,]?(\d+\.\d+|\d+°\d+\'\d+\.\d+"[EW])', text
                )
                if data:
                    properties = {
                        "name": data.group(1),
                        "lat": data.group(2),
                        "lon": data.group(3),
                    }
                    yield Feature(**properties)
