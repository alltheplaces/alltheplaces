import scrapy

from locations.dict_parser import DictParser


class RemaxEsSpider(scrapy.Spider):
    name = "remax_es"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.es"]
    start_urls = [
        "https://www.remax.es/buscador-de-oficinas/jsonData.php?classification=&type=&subtype=&bedrooms=&bathrooms=&caract=&price=&referencia=&codigopostal=&requery=&provincia=&city=&distrito=&anaconda=&favorite=0&collection=0&_=1671458112266"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for _, value in response.json().items():
            item = DictParser.parse(value)
            item["phone"] = value.get("contact_phone")
            item["lat"] = value.get("la")
            item["lon"] = value.get("lo")

            yield item
