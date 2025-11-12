from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature


class IntesaSanpaoloITSpider(Spider):
    name = "intesa_sanpaolo_it"
    item_attributes = {"brand": "Intesa Sanpaolo", "brand_wikidata": "Q1343118"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {
            "payload": {"latitudine": 41.95131997447626, "longitudine": 12.496400000000012, "numeroRisultati": 100000}
        }

        yield JsonRequest(
            url="https://api.intesasanpaolo.com/ib/content/api/app/public/filiale/ricercaFilialiGeoloc",
            data=data,
            callback=self.parse_bank,
        )
        yield JsonRequest(
            url="https://api.intesasanpaolo.com/ib/content/api/app/public/atm/ricercaAtmGeoloc",
            data=data,
            callback=self.parse_atm,
        )

    def parse_bank(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["payload"].get("listaFilialiGeoloc"):
            item = Feature()
            item["name"] = location["nomeBanca"]
            item["lat"] = location["latitudine"]
            item["lon"] = location["longitudine"]
            item["ref"] = location["chiave"] + "- Bank"
            item["street_address"] = location["indirizzo"]
            item["city"] = location["comune"]
            item["state"] = location["codiceProvincia"]
            item["phone"] = location.get("numeroTelefono")
            item["email"] = location["filiali"]["descEmail"]
            apply_category(Categories.BANK, item)
            item["opening_hours"] = OpeningHours()
            for day, time in location.get("orariMap", {}).items():
                day = sanitise_day(day.title(), DAYS_IT)
                open_time = time.get("oraApertura").replace(".", ":")
                close_time = time.get("oraChiusura").replace(".", ":")
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item

    def parse_atm(self, response, **kwargs):
        for location in response.json()["payload"]["listaAtmGeoloc"]:
            item = Feature()
            item["lat"] = location["latitudine"]
            item["lon"] = location["longitudine"]
            item["ref"] = location["chiave"] + "- ATM"
            item["name"] = location["descrizioneAzienda"]
            item["street_address"] = location["indirizzo"]
            item["city"] = location["comune"]
            item["state"] = location["codiceProvincia"]
            apply_category(Categories.ATM, item)
            yield item
