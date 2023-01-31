import json
import re

import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature


class CostaCoffeeUSSpider(scrapy.Spider):
    name = "costacoffee_us"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["us.costacoffee.com"]
    start_urls = ["https://us.costacoffee.com/amlocator/index/ajax"]

    def parse(self, response):
        script = response.xpath('//script[contains(text(), "amLocator")]/text()').extract_first()

        start = script.index("jsonLocations: ") + len("jsonLocations: ")
        stop = script.index("imageLocations")

        locations = script[start:stop].strip().strip(",")
        items = json.loads(locations)["items"]

        for store in items:
            item = Feature()
            item["ref"] = store["id"]
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            html = Selector(text=store["popup_html"])

            item["name"] = html.xpath('//*[@class="amlocator-title"]/text()').get()

            for line in html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
                line = line.strip()
                if m := re.match(r"City: (.*)", line):
                    item["city"] = m.group(1)
                elif m := re.match(r"Zip: (.*)", line):
                    item["postcode"] = m.group(1)
                elif m := re.match(r"Address: (.*)", line):
                    item["street_address"] = m.group(1)
                elif m := re.match(r"State: (.*)", line):
                    item["state"] = m.group(1)

            apply_category(Categories.COFFEE_SHOP, item)

            yield item
