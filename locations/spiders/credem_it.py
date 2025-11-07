import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations


class CredemITSpider(Spider):
    name = "credem_it"
    item_attributes = {"brand": "Credem", "brand_wikidata": "Q3696881"}

    async def start(self) -> AsyncIterator[Request]:
        for city in city_locations("IT", 15000):
            for location_type in ["bancomat", "filiale"]:
                body = f'lat={city["latitude"]}&lon={city["longitude"]}&{location_type}=true'
                yield Request(
                    url="https://www.credem.it/content/credem/it/contatti/ricerca-filiali.locator.json",
                    method="POST",
                    body=body,
                    headers={
                        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "referer": "https://www.credem.it/content/credem/it/contatti/ricerca-filiali.html",
                    },
                    callback=self.parse,
                    cb_kwargs={"location_type": location_type},
                )

    def parse(self, response: Response, location_type: str) -> Any:
        data = response.json().get("wrapped", {}).get("risultati", [])
        for location in data:
            uuid = location.get("uuid", "")
            if location_type == "bancomat" and not re.match(r"^\d+$", uuid):
                continue

            item = DictParser.parse(location)
            item["ref"] = f"{uuid} - {'ATM' if location_type == 'bancomat' else 'Bank'}"
            item["street_address"] = item.pop("addr_full", "")
            item["branch"] = location.get("nomeAgenzia", "")
            item["state"] = location.get("provincia", "")
            item["name"] = self.item_attributes["brand"]

            if location_type == "filiale":
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, bool(location.get("bancomat")))
            else:
                apply_category(Categories.ATM, item)

            yield item
