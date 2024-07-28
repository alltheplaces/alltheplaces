import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FiatDKSpider(scrapy.Spider):
    name = "fiat_dk"
    item_attributes = {"brand": "Fiat", "brand_wikidata": "Q27597"}
    start_urls = [
        "https://interaction.fiat.dk/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=f01f079120&lang=&load_all=1&layout=1"
    ]

    def parse(self, response, **kwargs):
        for dealer in response.json():
            item = DictParser.parse(dealer)
            apply_category(Categories.SHOP_CAR, item)
            yield item
