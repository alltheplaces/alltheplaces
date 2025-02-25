import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DiaBRSpider(scrapy.Spider):
    name = "dia_br"
    item_attributes = {"brand": "Dia", "brand_wikidata": "Q925132"}
    start_urls = ["https://www.dia.com.br/page-data/lojas/page-data.json"]

    def parse(self, response):
        for store in response.json()["result"]["data"]["lojas"]["nodes"]:
            store["street_address"] = store.pop("address")
            store["postcode"] = store.pop("cep")
            store["state"] = store.pop("district")
            item = DictParser.parse(store)
            item["website"] = f'https://www.dia.com.br/lojas/{store["slug"]}/'
            oh = OpeningHours()
            for day in DAYS:
                if day == "Su":
                    start_time = store["sundayOpen"]
                    close_time = store["sundayClose"]
                else:
                    start_time = store["mondayOpen"]
                    close_time = store["mondayClose"]
                if start_time != "00:00:00":
                    oh.add_range(day, start_time, close_time, time_format="%H:%M:%S")
            item["opening_hours"] = oh
            item["extras"] = {}
            if any(f["name"] == "Estacionamento" for f in store["services"]):
                item["extras"]["has_parking"] = "yes"
            if any(f["name"] == "Padaria" for f in store["services"]):
                item["extras"]["Refreshments"] = "yes"
            yield item
