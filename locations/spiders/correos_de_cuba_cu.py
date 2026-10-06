import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


def clean(value: str | None) -> str | None:
    value = re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip(" .,-")
    return value or None


class CorreosDeCubaCuSpider(Spider):
    name = "correos_de_cuba_cu"
    item_attributes = {"operator": "Correos de Cuba", "operator_wikidata": "Q5789322"}
    allowed_domains = ["www.correos.cu"]
    # The "Puntos de Servicios" page names the municipalities and provinces (as <select> options);
    # the office list itself comes from the site's REST API.
    start_urls = ["https://www.correos.cu/puntos-de-servicio/"]
    # The date is a "changed since" filter: an old date returns every office.
    offices_url = "https://www.correos.cu/wp-json/correos-api/oficinas/2000-01-01"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        provinces = {
            option.xpath("@value").get(): clean(option.xpath("text()").get())
            for option in response.xpath('//select[@id="id_provincia"]/option[@value!="0"]')
        }
        municipalities = {}
        for option in response.xpath('//select[@id="id_municipio"]/option[@value!="0"]'):
            province = option.xpath("@id").get()
            if province in ("16", "17"):
                province = "2"  # the eastern and western halves of La Habana have their own postal companies
            municipalities[option.xpath("@value").get()] = (
                clean(option.xpath("text()").get()),
                provinces.get(province),
            )
        yield JsonRequest(self.offices_url, callback=self.parse_offices, cb_kwargs={"municipalities": municipalities})

    def parse_offices(self, response: Response, municipalities: dict) -> Any:
        for office in response.json():
            if office["activa"] != "1":
                continue
            if office["id_tipo_oficina"] == "1":
                continue  # "Empresa": the head office of a provincial postal company, not a public counter

            item = Feature()
            item["ref"] = office["id"]
            item["branch"] = clean(office["nombre"])
            item["addr_full"] = clean(office["direccion"])
            item["postcode"] = clean(office["codigo_postal"])
            item["city"], item["state"] = municipalities.get(office["municipio_id"], (None, None))
            item["country"] = "CU"
            try:
                lat, lon = float(office["latitud"]), float(office["longitud"])
                if 19.5 < lat < 23.5 and -85.2 < lon < -74:
                    item["lat"], item["lon"] = lat, lon
            except (TypeError, ValueError):
                pass
            # Numbers are separated by commas, slashes, line breaks or just spaces: "72125542 72027824".
            phones = re.findall(r"(?:\+53\s?)?\d[\d-]{5,}\d", office["telefonos"] or "")
            item["phone"] = "; ".join(phones) or None
            # Opening hours are not emitted: nearly every office carries the same "08:00"/"18:00" pair with no
            # days attached, so it is not known which days it applies to.
            apply_category(Categories.POST_OFFICE, item)
            yield item
