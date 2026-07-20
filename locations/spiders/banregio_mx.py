import re
from typing import Any, AsyncIterator

import scrapy
from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class BanregioMXSpider(scrapy.Spider):
    name = "banregio_mx"
    item_attributes = {"brand": "Banregio", "brand_wikidata": "Q4853573"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    LOCATED_IN_MAPPINGS = [
        (["7 ELEVEN", "7-ELEVEN"], {"brand": "7-Eleven", "brand_wikidata": "Q259340"}),
        (["WALMART"], {"brand": "Walmart", "brand_wikidata": "Q483551"}),
        (["BODEGA AURRERA", "MI BODEGA"], {"brand": "Bodega Aurrera", "brand_wikidata": "Q3365858"}),
        (["HEB", "H-E-B"], {"brand": "H-E-B", "brand_wikidata": "Q830621"}),
        (["SORIANA"], {"brand": "Soriana", "brand_wikidata": "Q735562"}),
    ]

    async def start(self) -> AsyncIterator[Any]:
        yield scrapy.http.FormRequest(
            url="https://www.banregio.com/backend/ubicaciones.php", formdata={"ciudad": "", "estado": ""}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if store["TIPO"] == "C" or store["TIPO"] == "S":
                item = Feature()
                item["ref"] = store["ID"]
                item["branch"] = store["NOMBRE"]
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    store["NOMBRE"], self.LOCATED_IN_MAPPINGS, self
                )
                item["lat"] = store["LATITUD"]
                item["lon"] = store["LONGITUD"]
                item["addr_full"] = store["DOMICILIO"]
                item["city"] = store["CIUDAD"]
                item["state"] = store["ESTADO"]
                oh = OpeningHours()
                for start_day, end_day, open_time, close_time in re.findall(
                    r"(\w+)(?: a (\w+))? de (\d+:\d\d) a (\d+:\d\d)", store["HORARIO"]
                ):
                    start_day = sanitise_day(start_day, DAYS_ES)
                    end_day = sanitise_day(end_day, DAYS_ES)
                    if start_day and end_day:
                        for day in day_range(start_day, end_day):
                            oh.add_range(day, open_time, close_time)
                    elif start_day:
                        oh.add_range(start_day, open_time, close_time)
                item["opening_hours"] = oh
                if store["TIPO"] == "C":
                    apply_category(Categories.ATM, item)
                if store["TIPO"] == "S":
                    apply_category(Categories.BANK, item)
                yield item
