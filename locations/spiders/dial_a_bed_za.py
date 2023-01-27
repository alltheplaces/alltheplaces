import re

from scrapy import Selector, Spider

from locations.items import Feature


class DialABedZASpider(Spider):
    name = "dial_a_bed_za"
    item_attributes = {"brand": "Dial-a-Bed", "brand_wikidata": "Q116429178"}
    start_urls = ["https://www.dialabed.co.za/amlocator/index/ajax/"]

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]

            html = Selector(text=location["popup_html"])

            item["name"] = html.xpath('//div[@class="amlocator-title"]/a/text()').get()
            item["website"] = html.xpath('//div[@class="amlocator-title"]/a/@href').get()

            for line in html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
                line = line.strip()
                if m := re.match(r"(.*): (.*)", line):
                    if m.group(1) == "City":
                        item["city"] = m.group(2)
                    elif m.group(1) == "Address":
                        item["street_address"] = m.group(2)
                    elif m.group(1) == "Phone":
                        item["phone"] = m.group(2)

            yield item
