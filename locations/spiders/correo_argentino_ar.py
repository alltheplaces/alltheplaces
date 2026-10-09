import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Province codes used by the finder (the letter of each ISO 3166-2:AR code).
PROVINCES = {
    "A": "Salta",
    "B": "Buenos Aires",
    "C": "Ciudad Autónoma de Buenos Aires",
    "D": "San Luis",
    "E": "Entre Ríos",
    "F": "La Rioja",
    "G": "Santiago del Estero",
    "H": "Chaco",
    "J": "San Juan",
    "K": "Catamarca",
    "L": "La Pampa",
    "M": "Mendoza",
    "N": "Misiones",
    "P": "Formosa",
    "Q": "Neuquén",
    "R": "Río Negro",
    "S": "Santa Fe",
    "T": "Tucumán",
    "U": "Chubut",
    "V": "Tierra del Fuego",
    "W": "Corrientes",
    "X": "Córdoba",
    "Y": "Jujuy",
    "Z": "Santa Cruz",
}


class CorreoArgentinoARSpider(Spider):
    name = "correo_argentino_ar"
    item_attributes = {"operator": "Correo Argentino", "operator_wikidata": "Q4036566"}
    allowed_domains = ["www.correoargentino.com.ar"]
    api = "https://www.correoargentino.com.ar/sites/all/modules/custom/ca_forms/api/wsFacade.php"
    # robots.txt asks for "Crawl-delay: 10".
    custom_settings = {"DOWNLOAD_DELAY": 10, "CONCURRENT_REQUESTS": 1}
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.correoargentino.com.ar/formularios/sucursales",
    }

    async def start(self) -> AsyncIterator[FormRequest]:
        for province in PROVINCES:
            if province == "C":
                # The finder hard-codes a single locality for the city of Buenos Aires. Searched at the highest
                # priority so items appear straight away rather than after the locality lists.
                yield self.search(province, {"id": "5001", "nombre": "Ciudad Autónoma de Buenos Aires", "cp": None})
                continue
            yield FormRequest(
                self.api,
                formdata={"action": "localidadesconsucursales", "provincia": province},
                headers=self.headers,
                callback=self.parse_localities,
                cb_kwargs={"province": province},
                # Fetch every province's locality list before the (slow) per-locality searches.
                priority=10,
            )

    def parse_localities(self, response: Response, province: str) -> Any:
        for locality in response.json()["Localidades"]["lista"]:
            yield self.search(province, locality)

    def search(self, province: str, locality: dict) -> FormRequest:
        # Large cities tend to have round postcodes (e.g. 2000 Rosario, 5000 Córdoba); search those first.
        cp = str(locality.get("cp") or "")
        priority = 2 if cp.endswith("000") else 1 if cp.endswith("00") else 0
        return FormRequest(
            self.api,
            formdata={
                "action": "sucursales",
                "provincia": province,
                "localidad": str(locality["id"]),
                "nis": "",
                "servicios": "",
            },
            headers=self.headers,
            callback=self.parse_units,
            cb_kwargs={"province": province, "locality": locality},
            priority=11 if province == "C" else priority,
        )

    def parse_units(self, response: Response, province: str, locality: dict) -> Any:
        # The result is an HTML fragment with one <address> per unit, followed by that unit's map marker script.
        for chunk in response.text.split("<address>")[1:]:
            header = re.search(r"<strong>\s*([^:<]+?)\s*:\s*([^<]*?)\s*</strong>", chunk)
            if not header:
                continue
            kind, name = header.group(1).upper(), re.sub(r"\s+", " ", header.group(2))
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in re.split(r"<br\s*/?>|</br>", chunk.split("</address>")[0])[1:]
            ]
            lines = [line for line in lines if line]

            item = Feature()
            # Only the city of Buenos Aires results carry the unit code (NIS, e.g. "C5836"); elsewhere the
            # template placeholder "{nis}" is left in, so fall back to the locality and unit name.
            if nis := re.search(r'class="accordion-toggle unidadespostales"[^>]*rel="(\w+)"', chunk):
                item["ref"] = nis.group(1)
            else:
                item["ref"] = f"{locality['id']}-{kind}-{name}"
            item["street_address"] = lines[0] if lines else None
            item["city"] = lines[1] if len(lines) > 1 else locality["nombre"]
            item["postcode"] = locality.get("cp")
            item["state"] = PROVINCES[province]
            if marker := re.search(r"L\.marker\(\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]", chunk):
                item["lat"], item["lon"] = marker.group(1), marker.group(2)
            if hours := re.search(r"HORARIOS:\s*</strong>(.*?)</p>", chunk, re.S):
                item["opening_hours"] = self.parse_hours(hours.group(1))

            if kind in ("SUCURSAL", "AGENCIA"):
                # Branches, and smaller agencies in shopping centres and public buildings.
                item["branch"] = name
                item["extras"]["post_office:type"] = kind.title()
                apply_category(Categories.POST_OFFICE, item)
            elif kind == "UNIDAD POSTAL":
                # "Unidades postales" are counters run by third-party businesses (kiosks, stationers,
                # call shops, couriers) on behalf of Correo Argentino, e.g. "BALVANERA KIOSCO ZOE".
                item["name"] = name
                item["extras"]["post_office"] = "post_partner"
                apply_category(Categories.GENERIC_POI, item)
            else:
                self.logger.error("Unexpected unit type: %s (%s)", kind, item["ref"])
                continue
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        # e.g. "LUN A VIE 08.00 A 13.00 LUN A VIE 16.00 A 20.00 SAB 09.00 A 12.00", "MIE Y JUE 09.00 A 13.00",
        # "LUN A JUEV 12.00 A 19.00". Days are read by their first three letters. Not add_ranges_from_string: it reads
        # "MAR Y JUE" as Tuesday to Thursday.
        oh = OpeningHours()
        for first, sep, last, start, end in re.findall(
            r"([A-Z]{3})[A-Z]*(?:\s+(A|Y)\s+([A-Z]{3})[A-Z]*)?\s+(\d{1,2}[.:]\d{2})\s+A\s+(\d{1,2}[.:]\d{2})",
            text.upper(),
        ):
            first, last = sanitise_day(first, DAYS_ES), sanitise_day(last, DAYS_ES)
            if not first or (sep and not last):
                continue
            if sep == "A":
                days = day_range(first, last)
            elif sep == "Y":
                days = [first, last]
            else:
                days = [first]
            oh.add_days_range(days, start.replace(".", ":"), end.replace(".", ":"))
        return oh
