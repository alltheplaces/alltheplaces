import json

from scrapy import Selector, Spider

from locations.items import Feature


class EldiBESpider(Spider):
    name = "eldi_be"
    item_attributes = {"brand": "Eldi", "brand_wikidata": "Q3050500"}
    start_urls = ["https://www.eldi.be/nl/winkels"]

    def parse(self, response, **kwargs):
        data = json.loads(
            response.xpath('//script[contains(text(), "Amasty_Storelocator")]/text()').re_first(
                r"jsonLocations: ({.+}),"
            )
        )
        for location in data["items"]:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            popup_html = Selector(text=location["popup_html"])
            item["name"] = popup_html.xpath('//a[@class="amlocator-link"]/@title').get()
            item["website"] = popup_html.xpath('//a[@class="amlocator-link"]/@href').get()
            for line in popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
                line = line.strip()
                if line.startswith("Adres: "):
                    item["street_address"] = line.replace("Adres: ", "")
                elif line.startswith("Postcode: "):
                    item["postcode"] = line.replace("Postcode: ", "")

            yield item
