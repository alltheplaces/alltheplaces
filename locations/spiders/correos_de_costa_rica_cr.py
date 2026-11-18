import unicodedata
from typing import Any

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# ARESEP (the public-services regulator) publishes the post offices as open data, with coordinates,
# keyed by the same office code Correos uses ("CODIGO" == "Id_sucursal"). It is a 2017 survey, so the
# office list itself comes from Correos' live branch finder and ARESEP only supplies the location.
ARESEP_URL = (
    "https://mapas.aresep.go.cr/server/rest/services/I_Transporte_Externo_PII/I_Transporte_Externo_PII/MapServer/4/"
    "query?where=1%3D1&outFields=CODIGO,NOM_OFI&outSR=4326&f=geojson"
)
# Codes whose ARESEP name differs from the Correos name but which are the same office:
# 1000 "ADMINISTRACIÓN CENTRAL" (frente al Club Unión) is the Correo Central building.
SAME_OFFICE = {"1000"}


def normalise(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().upper()
    return name.removeprefix("SUCURSAL ").strip()


class CorreosDeCostaRicaCRSpider(Spider):
    name = "correos_de_costa_rica_cr"
    item_attributes = {"operator": "Correos de Costa Rica", "operator_wikidata": "Q5172894"}
    allowed_domains = ["mapas.aresep.go.cr", "sucursal.correos.go.cr"]
    start_urls = [ARESEP_URL]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = {}
        for feature in response.json()["features"]:
            code = (feature["properties"]["CODIGO"] or "").strip()
            if code and feature.get("geometry"):
                lon, lat = feature["geometry"]["coordinates"]
                locations[code] = (lat, lon, feature["properties"]["NOM_OFI"])
        # The branch finder (iframe on correos.go.cr/oficinas/) is a Laravel app: fetch the page for the
        # session cookie and CSRF token, then POST an empty search to list every office.
        yield Request(
            "https://sucursal.correos.go.cr/web/office", callback=self.parse_form, cb_kwargs={"locations": locations}
        )

    def parse_form(self, response: Response, locations: dict) -> Any:
        token = response.xpath('//meta[@name="csrf-token"]/@content').get()
        yield JsonRequest(
            "https://sucursal.correos.go.cr/web/office/search",
            data={"search": "", "province": ""},
            headers={"X-CSRF-TOKEN": token, "X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_offices,
            cb_kwargs={"locations": locations},
        )

    def parse_offices(self, response: Response, locations: dict) -> Any:
        for office in response.json():
            if office.get("estado") != 1:
                continue  # inactive
            code = office["Id_sucursal"].strip()
            item = Feature()
            item["ref"] = code
            item["name"] = " ".join(office["Nombre_sucursal"].split())
            item["branch"] = item["name"].removeprefix("Sucursal ").strip()
            item["addr_full"] = " ".join((office.get("Direccion") or "").split()) or None
            item["state"] = office.get("Provincia")
            item["phone"] = office.get("Telefono")
            item["extras"]["opening_hours:note"] = " ".join((office.get("Horario") or "").split()) or None
            item["website"] = "https://correos.go.cr/oficinas/"

            if office.get("Latitud") and office.get("Longitud"):
                item["lat"], item["lon"] = office["Latitud"], office["Longitud"]
            elif location := locations.get(code):
                lat, lon, aresep_name = location
                # Some codes were reassigned since 2017; only trust the match when the names agree.
                if (
                    code in SAME_OFFICE
                    or normalise(aresep_name)[:4] in normalise(item["name"])
                    or normalise(item["branch"])[:4] in normalise(aresep_name)
                ):
                    item["lat"], item["lon"] = lat, lon

            apply_category(Categories.POST_OFFICE, item)
            yield item
