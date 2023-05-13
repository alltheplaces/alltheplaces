import scrapy

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
    ]

    def start_requests(self):
        for country in self.available_countries:
            yield scrapy.Request(
                f"https://kong-proxy-aws.toyota-europe.com/dxp/dealers/api/toyota/{country}/{country}/drive/2.344148/48.862893?count=1000&extraCountries=&isCurrentLocation=false",
                callback=self.parse,
            )

    def parse(self, response):
        for store in response.json().get("dealers"):
            address_details = store["address"]
            coordinates = address_details["geo"]
            item = DictParser.parse(store)
            item["ref"] = store["uuid"]
            item["email"] = store["eMail"]
            item["lat"] = coordinates["lat"]
            item["lon"] = coordinates["lon"]
            item["country"] = store["country"].upper()
            yield item
