import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

BRANDS = {
    "SPAR EXPRESS": ({"name": "Spar Express"}, Categories.SHOP_CONVENIENCE),
    "SPAR": ({"name": "Spar"}, Categories.SHOP_CONVENIENCE),
    "EUROSPAR": ({"brand": "Eurospar", "brand_wikidata": "Q12309283"}, Categories.SHOP_SUPERMARKET),
    "SPAR NATURAL": ({"name": "Spar Natural"}, Categories.SHOP_CONVENIENCE),
    "SPAR CITY": ({"name": "Spar City"}, Categories.SHOP_CONVENIENCE),
}


class SparESSpider(scrapy.Spider):
    name = "spar_es"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}
    start_urls = ["https://spar.es/wp-admin/admin-ajax.php?lang=es&action=store_search&autoload=1"]

    def parse(self, response, **kwargs):
        for shop in response.json():
            shop["street_address"] = ", ".join(filter(None, [shop.pop("address"), shop.pop("address2")]))
            item = DictParser.parse(shop)
            store_type = "SPAR EXPRESS" if shop["store"].startswith("SPAR EXPRESS") else shop["store"]
            brand, category = BRANDS.get(store_type, ({}, None))
            item.update(brand)
            if category is not None:
                apply_category(category, item)

            yield item
