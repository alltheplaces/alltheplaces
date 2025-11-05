from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, OpeningHours


class BciCLSpider(Spider):
    name = "bci_cl"
    item_attributes = {"brand": "BCI", "brand_wikidata": "Q2882083"}

    def make_request(self, location_type: str, page: int, limit: int = 100) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.bci.cl/api/content/spaces/sucursales-y-cajeros/types/{location_type}/entries?per_page={limit}&page={page}",
            cb_kwargs=dict(location_type=location_type, page=page),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        for location_type in ["sucursal", "cajero", "centros-empresarios", "centros-nace"]:
            yield self.make_request(location_type, 1)

    def parse(self, response: Response, location_type: str, page: int) -> Any:
        for entry in response.json().get("entries", []):
            location = entry.get("fields", {}) | entry.get("meta", {})
            location.update(location.pop("Ubicación")[0])
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = location.get("location_street")
            item["state"] = location.get("administrative_area_level_2")
            item["city"] = location.get("administrative_area_level_3")
            item["phone"] = location.get("Teléfono")
            item["email"] = location.get("Correo")
            item["opening_hours"] = OpeningHours()
            item["country"] = "CL"
            for day in DAYS_ES:
                hours = location.get(f"Horario Funcionamiento {day}")
                if hours in [None, ["Cerrado"]]:
                    continue
                item["opening_hours"].add_range(DAYS_ES[day], *hours)

            if location.get("type") == "sucursal":
                apply_category(Categories.BANK, item)
            elif location.get("type") == "cajero":
                apply_category(Categories.ATM, item)
            elif location.get("type") == "centros-empresarios":
                apply_category(Categories.OFFICE_COMPANY, item)
            elif location.get("type") == "centros-nace":
                apply_category({"office": "coworking"}, item)
            yield item

        if page < response.json()["meta"]["total_pages"]:
            yield self.make_request(location_type, page + 1)
