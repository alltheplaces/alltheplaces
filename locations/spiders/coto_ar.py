import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class CotoARSpider(scrapy.Spider):
    name = "coto_ar"
    item_attributes = {"brand": "Coto", "brand_wikidata": "Q5175411"}
    start_urls = ["http://www.coto.com.ar/mapassucursales/Sucursales/ListadoSucursalesPorDistancia.json.aspx"]

    def parse(self, response, **kwargs):
        results = response.json()
        for data in results["results"]:
            opening_hours = OpeningHours()
            for days, field in [(DAYS[0:4], "hor_lu_a_ju"), (["Fr"], "hor_vi"), (["Sa"], "hor_sa"), (["Su"], "hor_do")]:
                if times := data.get(field):
                    if times == "Cerrado":
                        continue
                    times_split = times.split(" a ")
                    if len(times_split) == 2:
                        opening_hours.add_days_range(days, times_split[0], times_split[1])

            yield Feature(
                ref=data["id_suc"],
                lat=data["latitud"],
                lon=data["longitud"],
                name="Coto " + data["desc_suc"],
                country="AR",
                phone=data["telefono"],
                addr_full=data["direccion"],
                opening_hours=opening_hours,
            )
