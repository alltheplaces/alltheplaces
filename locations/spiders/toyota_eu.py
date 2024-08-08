import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ToyotaEUSpider(scrapy.Spider):
    name = "toyota_eu"
    item_attributes = {
        "brand": "Toyota",
        "brand_wikidata": "Q53268",
    }
    available_countries = [
        "tr",
        "az",
        "pl",
        "ru",
        "lv",
        "si",
        "lt",
        "ua",
        "pt",
        "se",
        "ba",
        "is",
        "sk",
        "de",
        "no",
        "ro",
        "es",
        "am",
        "hr",
        "hu",
        "fi",
        "ge",
        "fr",
        "nl",
        "gr",
        "it",
        "rs",
        "bg",
        "cz",
    ]

    def start_requests(self):
        for country in self.available_countries:
            yield scrapy.Request(
                f"https://kong-proxy-aws.toyota-europe.com/dxp/dealers/api/toyota/{country}/cs/all?extraCountries=&services=&randomize=false",
                callback=self.parse,
            )

    def parse(self, response):
        for store in response.json().get("dealers"):
            address_details = store["address"]
            coordinates = address_details["geo"]
            item = DictParser.parse(store)
            item["ref"] = store["id"]
            item["email"] = store["eMail"]
            item["lat"] = coordinates["lat"]
            item["lon"] = coordinates["lon"]
            item["country"] = store["country"].upper()

            apply_category(Categories.SHOP_CAR, item)

            yield item
