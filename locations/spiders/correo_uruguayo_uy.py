import csv
import io
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DEPARTMENTS = {
    "AR": "Artigas",
    "CA": "Canelones",
    "CL": "Cerro Largo",
    "CO": "Colonia",
    "DU": "Durazno",
    "FD": "Florida",
    "FS": "Flores",
    "LA": "Lavalleja",
    "MA": "Maldonado",
    "MO": "Montevideo",
    "PA": "Paysandú",
    "RN": "Río Negro",
    "RO": "Rocha",
    "RV": "Rivera",
    "SA": "Salto",
    "SJ": "San José",
    "SO": "Soriano",
    "TA": "Tacuarembó",
    "TT": "Treinta y Tres",
}
DAY = "|".join(sorted(map(re.escape, DAYS_ES), key=len, reverse=True))
DAYS_RE = re.compile(rf"\b({DAY})\b(?:\s*(a|y)\s*\b({DAY})\b)?(.*?)(?=\b(?:{DAY})\b|$)", re.IGNORECASE)
RANGE_RE = re.compile(r"(\d{1,2})(?:[.:](\d{2}))?\s*a\s*(\d{1,2})(?:[.:](\d{2}))?", re.IGNORECASE)


def clean(value: str | None) -> str | None:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value or None


class CorreoUruguayoUYSpider(Spider):
    name = "correo_uruguayo_uy"
    item_attributes = {"operator": "Correo Uruguayo", "operator_wikidata": "Q5172888"}
    allowed_domains = ["www.correo.com.uy"]
    # Open data that Correo Uruguayo publishes on its "Locales de Correo" page (required by the central bank for
    # every place offering postal money orders): its own branches ("SUC"), with coordinates and hours.
    start_urls = ["https://www.correo.com.uy/archivos/datos-abiertos/sucursales-y-puntos-de-atencion.csv"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        try:
            text = response.body.decode("utf-8")
        except UnicodeDecodeError:
            text = response.body.decode("latin-1")
        rows = csv.reader(io.StringIO(text), delimiter=";")
        header = [clean(h) for h in next(rows)]
        for row in rows:
            office = dict(zip(header, [clean(v) for v in row]))
            if office.get("Tipo de local") != "SUC":
                self.logger.warning("Unknown place type %s", office.get("Tipo de local"))
                continue

            item = Feature()
            item["ref"] = office["Codigo punto atencion"]
            item["branch"] = re.sub(r"^SUC\s+", "", office["Nombre del punto de atencion"] or "")
            item["lat"] = (office["Ubicacion - Latitud"] or "").replace(",", ".")
            item["lon"] = (office["Ubicacion - Longituc"] or "").replace(",", ".")
            item["street_address"] = office["Direccion"]
            department = office["Codigo Departamento"]
            item["state"] = DEPARTMENTS.get(department)
            place = (office["Barrio y Localidad o Ciudad"] or "").title() or None
            if department == "MO":
                item["city"] = "Montevideo"
                item["extras"]["addr:suburb"] = place  # a Montevideo neighbourhood ("Pocitos", "Cordon")
            else:
                item["city"] = place
            item["phone"] = office["Telefonos"]
            item["opening_hours"] = self.parse_hours(office["Horarios"] or "")
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        """Parse "Lunes a Viernes de 9 a 14 y de 14.45 a 17 hs - Sabado y Domingo de 10 a 22 hs"."""
        # Not add_ranges_from_string: it reads "Martes y Jueves 8 a 12 hs" as Tuesday to Thursday.
        oh = OpeningHours()
        found = False
        for first, joiner, last, rest in DAYS_RE.findall(text):
            first = sanitise_day(first, DAYS_ES)
            if not last:
                days = [first]
            elif joiner.lower() == "a":
                days = day_range(first, sanitise_day(last, DAYS_ES))
            else:
                days = [first, sanitise_day(last, DAYS_ES)]  # "Martes y Jueves"
            ranges = RANGE_RE.findall(rest)
            if not ranges:
                return None
            for open_h, open_m, close_h, close_m in ranges:
                for day in days:
                    oh.add_range(day, f"{open_h}:{open_m or '00'}", f"{close_h}:{close_m or '00'}", "%H:%M")
            found = True
        return oh if found else None
