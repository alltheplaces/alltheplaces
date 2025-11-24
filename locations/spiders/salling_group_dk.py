import re

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.carls_jr_us import CarlsJrUSSpider
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES

BRANDS = {
    "bilka": ({"brand": "Bilka", "brand_wikidata": "Q861880"}, Categories.SHOP_SUPERMARKET),
    "br": ({"brand": "BR", "brand_wikidata": "Q4353228"}, Categories.SHOP_TOYS),
    "carlsjr": (CarlsJrUSSpider.item_attributes, Categories.FAST_FOOD),
    "foetex": ({"brand": "Føtex", "brand_wikidata": "Q1480395"}, Categories.SHOP_SUPERMARKET),
    "netto": ({"brand": "Netto", "brand_wikidata": "Q552652"}, Categories.SHOP_SUPERMARKET),
    "salling": ({"brand": "Salling", "brand_wikidata": "Q68166349"}, Categories.SHOP_DEPARTMENT_STORE),
    "starbucks": (STARBUCKS_SHARED_ATTRIBUTES, Categories.COFFEE_SHOP),
}


class SallingGroupDKSpider(scrapy.Spider):
    name = "salling_group_dk"
    start_urls = ["https://www.foetex.dk/_nuxt/app.js"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        if token := re.search(r"Bearer.+?concat\(\w\|\|\"([-\w]+)\"", response.text):
            yield JsonRequest(
                url="https://api.sallinggroup.com/v2/stores?per_page=10000",
                headers={"Authorization": f"Bearer {token.group(1)}"},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street", "")
            item["lon"], item["lat"] = store.get("coordinates", [None, None])

            if store["brand"] in ["netto", "starbucks"]:
                continue  # POIs already covered by netto_salling & starbucks_eu spider

            if store["brand"] in BRANDS:
                item.update(BRANDS[store["brand"]][0])
                apply_category(BRANDS[store["brand"]][1], item)
            else:
                self.logger.error("Unexpected brand: {}".format(store.get("brand")))

            yield item
