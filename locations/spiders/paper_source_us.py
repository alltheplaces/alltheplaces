import re

from scrapy import Selector, Spider

from locations.items import GeojsonPointItem


class PaperSourceUSSpider(Spider):
    name = "paper_source_us"
    item_attributes = {"brand": "Paper Source", "brand_wikidata": "Q25000269"}
    start_urls = ["https://www.papersource.com/amlocator/index/ajax/"]

    def parse(self, response, **kwargs):
        for store in response.json()["items"]:
            item = GeojsonPointItem()
            item["ref"] = store["id"]
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            html = Selector(text=store["popup_html"])

            item["name"] = html.xpath('//div[@class="amlocator-title"]/a/text()').get()
            item["website"] = html.xpath('//div[@class="amlocator-title"]/a/@href').get()

            for line in html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
                line = line.strip()
                if match := re.match(r"(.*): (.*)", line):
                    if match.group(1) == "Phone":
                        item["phone"] = match.group(2)
                    elif match.group(1) == "Address":
                        item["street_address"] = match.group(2)
                    elif match.group(1) == "City":
                        item["city"] = match.group(2)
                    elif match.group(1) == "State":
                        item["state"] = match.group(2)
                    elif match.group(1) == "Zip":
                        item["postcode"] = match.group(2)

            yield item
