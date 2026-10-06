import csv
import io
import re
import zipfile
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class CorreosESSpider(Spider):
    name = "correos_es"
    item_attributes = {"operator": "Correos", "operator_wikidata": "Q776605"}
    allowed_domains = ["descargas.correos.es"]
    # Correos publishes its post offices and rural service points as a daily file:
    # https://www.correos.es/es/es/empresas/bases-de-datos-de-puntos-de-entrega
    start_urls = ["https://descargas.correos.es/Publico/conviert/Oficinas.zip"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
            name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
            text = archive.read(name).decode("utf-8")
        for row in csv.DictReader(io.StringIO(text), delimiter=";"):
            item = Feature()
            item["ref"] = row["CODIGO"]
            item["branch"] = row["DESCRIPCION"]
            item["lat"], item["lon"] = row["LATITUD WGS 84"], row["LONGITUD WGS 84"]
            item["postcode"] = row["LOCALIZACION CP"]
            item["city"] = row["LOCALIZACION (localidad)"]
            item["street_address"] = row["LOCALIZACION (domicilio)"]
            item["state"] = row["PROVINCIA"]
            item["phone"] = row["TELEFONO"]
            item["opening_hours"] = self.parse_hours(row["HORARIO"])
            # OFICINA: a post office. PUNTOATENCIONRURAL: a rural service point staffed by Correos for a
            # set time each day.
            apply_category(Categories.POST_OFFICE, item)
            if row["CODTIPO"] == "PUNTOATENCIONRURAL":
                item["extras"]["post_office:type"] = "rural_service_point"
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        # "L-V: DE 08:30 A 14:30 Y DE 16:30 A 20:00/S: SIN SERVICIO/Festivos: SIN SERVICIO"
        oh = OpeningHours()
        for part in text.split("/"):
            label, _, ranges = part.partition(":")
            days = {"L-V": DAYS[:5], "S": ["Sa"], "D": ["Su"]}.get(label.strip())
            if not days:
                continue
            for start, end in re.findall(r"DE (\d{2}:\d{2}) A (\d{2}:\d{2})", ranges):
                for day in days:
                    oh.add_range(day, start, end)
        return oh
