from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class BancoMacroARSpider(Spider):
    name = "banco_macro_ar"
    item_attributes = {"brand": "Macro", "brand_wikidata": "Q2335199"}

    async def start(self) -> AsyncIterator[Request]:
        # Bulk endpoints behind the branch/ATM finder (banco=BM = Banco Macro). The API needs an
        # "Accept: application/json" header (a request without it gets HTTP 400), but JsonRequest can't
        # be used: its "Content-Type: application/json" header makes the endpoint return an empty body.
        # The "UNegocio_BusquedaComercios" endpoint is skipped: it lists third-party merchants
        # (Carrefour, etc.) offering cash withdrawal, not Macro locations.
        yield Request(
            url="https://www.macro.com.ar/interfaces/UNegocio_BusquedaSucursales/V1/R0/?banco=BM&datosCompletos=true",
            headers={"Accept": "application/json"},
            cb_kwargs={"location_type": "branch"},
        )
        yield Request(
            url="https://www.macro.com.ar/interfaces/UNegocio_BusquedaCajeros/V1/R0/?banco=BM",
            headers={"Accept": "application/json"},
            cb_kwargs={"location_type": "atm"},
        )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        elements = response.json()["elements"]
        # A coordinate shared across more than one province is a geocoding-failure placeholder
        # (one point is pinned to ATMs in 8 different provinces), not a real location.
        provinces_per_coordinate: dict[tuple, set] = {}
        for location in elements:
            key = (location.get("latitud"), location.get("longitud"))
            provinces_per_coordinate.setdefault(key, set()).add(location.get("provincia"))

        for location in elements:
            coordinate = (location.get("latitud"), location.get("longitud"))
            if not self._valid_coordinates(location) or len(provinces_per_coordinate[coordinate]) > 1:
                continue  # drop corrupt or placeholder coordinates

            item = DictParser.parse(location)
            item["state"] = location.get("provincia")  # DictParser otherwise maps a region/division here
            item["city"] = location.get("localidad")
            item["postcode"] = location.get("codpostal")
            item["street_address"] = location.get("domicilio")

            if location_type == "branch":
                if location.get("habilitada") != "SI":  # skip disabled / non-operational branches
                    continue
                # "codigo" is a shared zone code, not a branch id; the address identifies each branch
                # and collapses the feed's duplicate metadata rows.
                item["ref"] = "{}, {}".format(location["domicilio"], location["localidad"])
                item["branch"] = item.pop("name", None)  # DictParser maps "nombre"
                item.pop("phone", None)  # "telefono" is a multi-number "/"-joined string, not a clean phone
                # "horario" is only a time range with no weekdays ("08:00 a 13:00"), so no opening_hours.
                apply_yes_no(Extras.WIFI, item, location.get("wifi") == "SI")
                apply_category(Categories.BANK, item)
            else:
                item["ref"] = location["codigo"]  # unique ATM code, e.g. "S1CBM533"
                apply_category(Categories.ATM, item)

            yield item

    def _valid_coordinates(self, location: dict) -> bool:
        try:
            lat, lon = float(location["latitud"]), float(location["longitud"])
        except (TypeError, ValueError, KeyError):
            return False
        # Reject corrupt values (lat == lon, projected UTM, points outside Argentina).
        return lat != lon and -56 < lat < -21 and -74 < lon < -53
