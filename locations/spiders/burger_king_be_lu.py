import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.spiders.burger_king import BurgerKingSpider


class BurgerKingBELUSpider(scrapy.Spider):
    name = "burger_king_be_lu"
    item_attributes = BurgerKingSpider.item_attributes
    start_urls = ["https://stores.burgerking.be/nl/"]

    def parse(self, response, **kwargs):
        for ld in LinkedDataParser.iter_linked_data(response):
            if ld["@type"] == "LocalBusiness":
                yield LinkedDataParser.parse_ld(ld)
