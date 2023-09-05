import json
from gzip import decompress

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DiaESSpider(Spider):
    name = "dia_es"
    item_attributes = {"brand": "Dia", "brand_wikidata": "Q925132"}
    allowed_domains = ["www.dia.es"]
    start_urls = ["https://www.dia.es/tiendas/buscador-tiendas-folletos"]

    def parse(self, response):
        store_list_url = response.xpath('.//input[@id="gz"]/@value').get()
        yield Request(url=store_list_url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        locations = json.loads(decompress(response.body).decode("utf-8"))
        for location in locations:
            store_id = location["idTienda"]
            yield JsonRequest(
                url=f"https://www.dia.es/tiendas/buscadorTiendas.html?action=buscarInformacionTienda&id={store_id}",
                meta={"lat": location["posicionX"], "lon": location["posicionY"]},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            "ref": response.json()["tiendaId"],
            "lat": response.meta["lat"],
            "lon": response.meta["lon"],
            "street_address": response.json()["direccionPostal"].strip(),
            "housenumber": response.json()["numeroVia"].strip(),
            "street": response.json()["nombreVia"].strip() + " " + response.json()["tipoVia"].strip(),
            "city": response.json()["localidad"].strip(),
            "postcode": response.json()["codigoPostal"].strip(),
        }
        properties["opening_hours"] = OpeningHours()
        for day_number, day_hours in response.json()["horariosTienda"].items():
            if "|" in day_hours:
                for day_hours_range in day_hours.split(" | "):
                    properties["opening_hours"].add_range(
                        DAYS[int(day_number) - 1], *day_hours_range.split(" - ", 1), "%H:%M"
                    )
            else:
                properties["opening_hours"].add_range(DAYS[int(day_number) - 1], *day_hours.split(" - ", 1), "%H:%M")
        yield Feature(**properties)
