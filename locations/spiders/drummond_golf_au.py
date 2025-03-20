import json
import re

import scrapy
from scrapy import Selector

from locations.categories import apply_category
from locations.dict_parser import DictParser


class DrummondGolfAUSpider(scrapy.Spider):
    name = "drummond_golf_au"
    item_attributes = {"brand": "Drummond Golf", "brand_wikidata": "Q124065894"}
    start_urls = ["https://www.drummondgolf.com.au/amlocator/index/ajax/?p=1"]

    def parse(self, response, **kwargs):
        if raw_data := re.search(r"items\":(\[.*\]),\"", response.text):
            for store in json.loads(raw_data.group(1)):
                item = DictParser.parse(store)
                popup_html = Selector(text=store["popup_html"])
                item["website"] = popup_html.xpath('//*[@class= "amlocator-link"]/@href').get().replace(" ", "")
                address_string = re.sub(r"\s+", " ", " ".join(filter(None, popup_html.xpath("//text()").getall())))
                item["city"] = address_string.split("City: ", 1)[1].split(" Zip: ", 1)[0]
                item["postcode"] = address_string.split("Zip: ", 1)[1].split(" Address: ", 1)[0]
                item["street_address"] = address_string.split("Address: ", 1)[1].split(" State: ", 1)[0]
                item["state"] = address_string.split("State: ", 1)[1].split(" Description: ", 1)[0]
                apply_category({"shop": "golf"}, item)
                yield item
            if next_url := re.search(r"action next.*href=\\\"(.*)\"\s*rel", response.text):
                yield scrapy.Request(url=next_url.group(1).replace("\\", ""), callback=self.parse)
