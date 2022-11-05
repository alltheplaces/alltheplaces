import re

import scrapy
from scrapy import Selector

from locations.items import GeojsonPointItem


class CostaCoffeeUSSpider(scrapy.Spider):
    name = "costacoffee_us"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["us.costacoffee.com"]
    start_urls = ["https://us.costacoffee.com/amlocator/index/ajax"]

    def parse(self, response):
        for store in response.json()["items"]:
            item = GeojsonPointItem()
            item["ref"] = store["id"]
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            html = Selector(text=store["popup_html"])

            item["name"] = html.xpath('//*[@class="amlocator-title"]/text()').get()

            for line in html.xpath(
                '//div[@class="amlocator-info-popup"]/text()'
            ).getall():
                line = line.strip()
                if m := re.match(r"City: (.*)", line):
                    item["city"] = m.group(1)
                elif m := re.match(r"Zip: (.*)", line):
                    item["postcode"] = m.group(1)
                elif m := re.match(r"Address: (.*)", line):
                    item["street_address"] = m.group(1)
                elif m := re.match(r"State: (.*)", line):
                    item["state"] = m.group(1)

            yield item
