from json import loads
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class EldiBESpider(AmastyStoreLocatorSpider):
    name = "eldi_be"
    item_attributes = {"brand": "Eldi", "brand_wikidata": "Q3050500"}
    start_urls = ["https://www.eldi.be/nl/winkels"]

    def parse(self, response: Response):
        yield from self.parse_features(
            loads(
                response.xpath('//script[contains(text(), "Amasty_Storelocator")]/text()').re_first(
                    r"jsonLocations: ({.+}),"
                )
            )["items"]
        )

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        for line in popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
            line = line.strip()
            if line.startswith("Adres: "):
                item["street_address"] = line.replace("Adres: ", "")
            elif line.startswith("Postcode: "):
                item["postcode"] = line.replace("Postcode: ", "")

        yield item
