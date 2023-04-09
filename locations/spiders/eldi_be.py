import json

from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class EldiBESpider(AmastyStoreLocatorSpider):
    name = "eldi_be"
    item_attributes = {"brand": "Eldi", "brand_wikidata": "Q3050500"}
    start_urls = ["https://www.eldi.be/nl/winkels"]

    def parse(self, response, **kwargs):
        yield from self.parse_items(
            json.loads(
                response.xpath('//script[contains(text(), "Amasty_Storelocator")]/text()').re_first(
                    r"jsonLocations: ({.+}),"
                )
            )["items"]
        )

    def parse_item(self, item, location, popup_html):
        for line in popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
            line = line.strip()
            if line.startswith("Adres: "):
                item["street_address"] = line.replace("Adres: ", "")
            elif line.startswith("Postcode: "):
                item["postcode"] = line.replace("Postcode: ", "")

        yield item
