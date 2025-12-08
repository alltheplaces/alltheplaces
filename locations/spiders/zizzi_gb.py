import scrapy

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class ZizziGBSpider(scrapy.Spider):
    name = "zizzi_gb"
    item_attributes = {"brand": "Zizzi", "brand_wikidata": "Q8072944"}
    start_urls = ["https://www.zizzi.co.uk/wp-json/locations/get_venues"]

    def parse(self, response):
        for store in response.json()["data"]:
            item = DictParser.parse(store)
            item["addr_full"] = clean_address(store["address"].split("\r\n"))
            item["image"] = store["featured_image"]
            item["website"] = store["link"]

            if store["region"] == "Ireland":
                item.pop("state")
                item["country"] = "IE"
            else:
                item["country"] = "GB"

            yield item
