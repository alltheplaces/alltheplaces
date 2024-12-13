import scrapy
import xmltodict

from locations.dict_parser import DictParser


class LagerhausATSpider(scrapy.Spider):
    name = "lagerhaus_at"
    item_attributes = {"brand": "Lagerhaus", "brand_wikidata": "Q1232873"}
    start_urls = [
        "https://static.lagerhaus.at/loc/v1/find/locations/full?lat=47.2&lon=16.2&distance=1660&divisions=Fachhandel%2FShop"
    ]

    def parse(self, response):
        obj = xmltodict.parse(response.text)
        for store in DictParser.get_nested_key(obj, "item"):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item.pop("country")
            item["street_address"] = store["address"]["line"]
            item["website"] = "https://lagerhaus.at/standort/" + store["id"]
            yield item
