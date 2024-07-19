import scrapy

from locations.dict_parser import DictParser


class BirkenstockSpider(scrapy.Spider):
    name = "birkenstock"
    item_attributes = {
        "brand": "Birkenstock",
        "brand_wikidata": "Q648458",
    }
    allowed_domains = ["birkenstock.com"]

    def start_requests(self):
        countries = {
            "EU": [
                "en_ES",
                "en_PT",
                "en_PL",
                "en_NL",
                "en_LU",
                "en_IT",
                "en_IE",
                "en_HU",
                "en_GR",
                "en_DK",
                "en_CZ",
                "en_HR",
            ],
            "DE": ["de_AT", "en_DE"],
            "GB": ["en_GB"],
            "JP": ["js_JP"],
            "US": ["en_US"],
        }
        for key, value in countries.items():
            for country in value:
                url = f"https://www.birkenstock.com/on/demandware.store/Sites-{key}-Site/{country}/Stores-GetStoresJson?&storeLocatorType=regular&storetype1=true"
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for _, data in response.json().get("stores").items():
            item = DictParser.parse(data)
            item["website"] = data.get("storeDetailsFlyinLink")

            if data.get("phoneAreaCode"):
                item["phone"] = f'{data.get("phoneAreaCode")} {item["phone"]}'

            yield item
