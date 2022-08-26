from scrapy import Spider

from locations.dict_parser import DictParser


class GreggsGBSpider(Spider):
    name = "greggs_gb"
    item_attributes = {"brand": "Greggs", "brand_wikidata": "Q3403981"}
    start_urls = ["https://production-digital.greggs.co.uk/api/v1.0/shops"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store["address"])
            item["phone"] = store["address"]["phoneNumber"]
            item["name"] = store["shopName"]
            item["ref"] = store["shopCode"]
            yield item
