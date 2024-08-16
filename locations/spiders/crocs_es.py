import scrapy
import xmltodict

from locations.dict_parser import DictParser
from locations.spiders.crocs_eu import CrocsEUSpider


class CrocsESSpider(scrapy.Spider):
    name = "crocs_es"
    item_attributes = CrocsEUSpider.item_attributes

    def start_requests(self):
        yield scrapy.Request(
            url="https://crocs.es/storefinder?ajax=1&all=1",
            method="POST",
        )

    def parse(self, response):
        json_data = xmltodict.parse(response.text)
        for data in json_data["markers"]["marker"]:
            for k in list(data.keys()):
                data[k[1:]] = data.pop(k)
            item = DictParser.parse(data)
            item["ref"] = data["id_store"]
            item["addr_full"] = data["addressNoHtml"]
            item["website"] = data["link"]
            yield item
