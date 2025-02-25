from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DiaBRSpider(Spider):
    name = "dia_br"
    item_attributes = {"brand": "Dia", "brand_wikidata": "Q925132"}
    start_urls = ["https://www.dia.com.br/page-data/lojas/page-data.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["result"]["data"]["lojas"]["nodes"]:
            store["street_address"] = store.pop("address")
            store["postcode"] = store.pop("cep")
            store["state"] = store.pop("district")

            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
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

            services = [s["name"] for s in store["services"]]
            apply_yes_no("parking_facility", item, "Estacionamento" in services)
            apply_yes_no("food", item, "Padaria" in services)

            yield item
