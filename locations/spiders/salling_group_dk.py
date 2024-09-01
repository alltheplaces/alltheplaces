import re

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser


class SallingGroupDKSpider(scrapy.Spider):
    name = "salling_group_dk"
    start_urls = ["https://www.foetex.dk/_nuxt/app.js"]
    brands = {
        "netto": {"brand": "Netto", "brand_wikidata": "Q552652"},
        "foetex": {
            "brand": "føtex",
            "brand_wikidata": "Q1480395",
            "extras": Categories.SHOP_SUPERMARKET.value,
            "website": "https://www.foetex.dk/kundeservice/find-din-foetex/",
        },
        "bilka": {
            "brand": "Bilka",
            "brand_wikidata": "Q861880",
            "extras": Categories.SHOP_SUPERMARKET.value,
            "website": "https://www.bilka.dk/kundeservice/info/find-din-bilka/c/find-din-bilka/",
        },
        "br": {
            "brand": "BR",
            "brand_wikidata": "Q4353228",
            "extras": Categories.SHOP_TOYS.value,
            "website": "https://www.br.dk/kundeservice/find-din-br/",
        },
        "salling": {
            "brand": "Salling",
            "brand_wikidata": "Q68166349",
            "extras": Categories.SHOP_DEPARTMENT_STORE.value,
            "website": "https://salling.dk/kundeservice/abningstider/",
        },
        "starbucks": {"brand": "Starbucks", "brand_wikidata": "Q37158", "extras": Categories.COFFEE_SHOP.value},
        "carlsjr": {"brand": "Carl's Jr", "brand_wikidata": "Q1043486", "website": "https://carlsjr.dk/find-os/"},
    }
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

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
            if brand := self.brands.get(store.get("brand")):
                if store["brand"] in ["netto", "starbucks"]:
                    continue  # POIs already covered by netto_salling & starbucks_eu spider
                item.update(brand)
            yield item
