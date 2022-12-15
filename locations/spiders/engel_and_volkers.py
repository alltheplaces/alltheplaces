import json
import re

import scrapy

from locations.dict_parser import DictParser


class EngelAndVolkersSpider(scrapy.Spider):
    name = "engel_and_volkers"
    item_attributes = {
        "brand": "Engel&Volkers",
        "brand_wikidata": "Q1341765",
    }
    allowed_domains = ["engelvoelkers.com"]
    start_urls = ["https://www.engelvoelkers.com/api/?source=locations&bu=&jsonp=markerinit_map_offices"]

    def parse(self, response):
        data = response.text.replace("markerinit_map_offices(", "").replace(");", "")
        data_json = json.loads(data)
        for agence in data_json["response"]:
            template_url = "https://www.engelvoelkers.com/api/?source=locations&jsonp=markerdetail_map_offices_{}&id={}"
            yield scrapy.Request(
                template_url.format(agence["id"], agence["id"]),
                callback=self.agence_parse,
            )

    def agence_parse(self, response):
        id = re.findall("id=[0-9]*", response.url)[0].replace("id=", "")
        data = response.text.replace(f"markerdetail_map_offices_{id}(", "").replace(");", "")
        data_json = json.loads(data)
        agence = data_json["response"]
        item = DictParser.parse(agence)
        item["name"] = agence.get("name", {}).get("en")
        item["website"] = agence.get("contact", {}).get("www")

        yield item
