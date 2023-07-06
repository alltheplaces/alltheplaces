import json

from scrapy import Spider

from locations.dict_parser import DictParser


class AromaRSSpider(Spider):
    name = "aroma_rs"
    item_attributes = {"brand": "Арома", "brand_wikidata": "Q116446961"}
    start_urls = ["https://aromamarketi.rs/lokacije/"]

    def parse(self, response, **kwargs):
        data = response.xpath('//script[@class="module__store_finder__storedata"]/text()').get()

        for location in json.loads(data):
            item = DictParser.parse(location["location"])
            item["country"] = location["location"]["country_short"]
            item["ref"] = item["name"] = location["title"]

            yield item
