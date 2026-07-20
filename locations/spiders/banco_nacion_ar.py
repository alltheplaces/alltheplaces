import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class BancoNacionARSpider(Spider):
    name = "banco_nacion_ar"
    item_attributes = {"brand": "Banco Nación", "brand_wikidata": "Q2883376"}

    async def start(self) -> AsyncIterator[Any]:
        # The locator returns results only for a selected province (province 0 = "none" -> empty), so
        # query each Argentine province id from the locator's dropdown (there is no 1 or 3). All five
        # boolean filter flags are required or the endpoint returns HTTP 500. The SUCURSALES view lists
        # every branch; the CAJEROS view additionally returns the standalone "extrabancario" ATMs
        # (airports, hospitals, universities, ...) that are located away from a branch.
        for location_type, criterion in (("branch", "SUCURSALES"), ("atm", "CAJEROS")):
            for province in (2, *range(4, 27)):
                yield JsonRequest(
                    url="https://www.bna.com.ar/SucursalesCajeros/_BuscarSucursalesyCajeros"
                    "?criterioDeBusqueda={}&provincia={}&localidad=0&novidentes=false&puntoEfectivo=false"
                    "&exclusivoClientes=false&centroAtencionEmpresas=false&tas=false".format(criterion, province),
                    cb_kwargs={"location_type": location_type},
                )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for location in response.json():
            # The CAJEROS view also repeats every branch (those rows have no "nombre"); the branches are
            # already yielded from the SUCURSALES view, so keep only the standalone ATM records here.
            if location_type == "atm" and not location.get("nombre"):
                continue

            item = DictParser.parse(location)  # maps latitud/longitud and "direccion" (-> addr_full)
            item["street_address"] = item.pop("addr_full", None)  # "direccion" is the street line only
            item["city"] = location.get("LOC_Nombre")
            item["state"] = location.get("PRO_Nombre")  # Argentine province

            if location_type == "branch":
                item["ref"] = str(location["suc_codcasa"])
                item["branch"] = location["sucursal"]
                item["postcode"] = location.get("SUC_codigopostal")
                if (area_code := location.get("SUC_prefijo")) and (telephone := location.get("SUC_telefono")):
                    item["phone"] = "{} {}".format(area_code, telephone)
                # ATMs are reported only as a per-branch count in the "textoCajeros" summary
                # ("Total cajeros: N", shown for every branch incl. 0), so the branch carries atm=yes/no.
                if atm_count := re.search(r"Total cajeros:\s*(\d+)", location.get("textoCajeros") or ""):
                    apply_yes_no(Extras.ATM, item, int(atm_count.group(1)) > 0, apply_positive_only=False)
                apply_category(Categories.BANK, item)
            else:
                item["ref"] = str(location["id_entidad"])
                # Keep the venue label but drop trailing "ATM"/"EXTRABANCARIO" service words
                # (some records are only those words, leaving no real name).
                item["name"] = (
                    re.sub(r"(\s*\b(?:ATM|EXTRABANCARIO)\b)+$", "", location["nombre"], flags=re.IGNORECASE).strip()
                    or None
                )
                # "horarioAtencion" is a uniform "24hs" on every ATM, including ones inside venues that
                # clearly close (universities, hospitals, public offices), so it is an unreliable default
                # and no opening_hours is emitted.
                apply_category(Categories.ATM, item)

            yield item
