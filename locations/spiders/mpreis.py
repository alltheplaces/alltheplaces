import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MpreisSpider(scrapy.Spider):
    name = "mpreis"
    item_attributes = {"brand": "MPreis", "brand_wikidata": "Q873491"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://cms-storefront.mpreis.at/c3_custom_data/location/index.json"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["postcode"] = str(store["plz"])
            item["city"] = store["ort"]
            item["name"] = store["vertriebslinie"]
            item["street_address"] = store["adresse"]
            item["phone"] = store["telefon"]
            if "MINIM" in store["vertriebslinie"]:
                item["brand"] = "miniM"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif "Tankstellenshop" in store["vertriebslinie"]:
                # Shop is MPREIS but the fuel station is not MPREIS brand
                item["brand"] = "MPREIS"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            else:
                item["brand"] = "MPREIS"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
