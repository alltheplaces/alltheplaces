import scrapy

from locations.dict_parser import DictParser


class PigglyWigglySpider(scrapy.Spider):
    name = "pigglywiggly"
    item_attributes = {"brand": "Piggly Wiggly", "brand_wikidata": "Q3388303"}
    allowed_domains = ["pigglywiggly.com"]
    start_urls = [
        "https://api.freshop.com/1/stores?app_key=piggly_wiggly_nc&has_address=true&limit=-1&token=198b3e8a2e1ff0f4c72bbdffe9b24a8c"
    ]

    def parse(self, response):
        for data in response.json().get("items"):
            item = DictParser.parse(data)
            item["street_address"] = data.get("address_1")

            yield item
