import re
import unicodedata

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Day-range phrases used in the "horario" field, mapped to the day
# abbreviations they cover.
DAY_RANGE_PHRASES = {
    "Lunes a Sábado": ["Mo", "Tu", "We", "Th", "Fr", "Sa"],
    "Lunes a Viernes": ["Mo", "Tu", "We", "Th", "Fr"],
    "Sábados": ["Sa"],
    "Sábado": ["Sa"],
    "Domingos y Festivos": ["Su"],
}
DAY_RANGE_RE = re.compile(
    "(" + "|".join(re.escape(phrase) for phrase in DAY_RANGE_PHRASES) + r")\s*(?:de\s*)?"
    r"((?:\d{1,2}:\d{2}\s*a\s*\d{1,2}:\d{2}\s*(?:y\s*(?:de\s*)?)?)+)"
)
TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2})\s*a\s*(\d{1,2}:\d{2})")

# ISO 3166-2:ES subdivision codes for the "comunidad" values seen in the
# store finder data.
STATE_CODES = {
    "Comunidad de Madrid": "MD",
    "Castilla-La Mancha": "CM",
    "Castilla y León": "CL",
}


def slugify_es(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return value.lower().replace(" ", "-")


class AhorramasESSpider(Spider):
    name = "ahorramas_es"
    item_attributes = {"brand": "Ahorramás", "brand_wikidata": "Q58221883"}
    # Search from central Madrid with a radius large enough to cover the
    # whole of the chain's Madrid/Castilla region footprint; this returns
    # the same complete set of stores regardless of search origin or a
    # further increased radius, so it is not a partial/geo-limited result.
    start_urls = [
        "https://www.ahorramas.com/on/demandware.store/Sites-Ahorramas-Site/es/Stores-FindStore"
        "?update=true&showMap=false&radius=1000&lat=40.4168&long=-3.7038&postalCodeInput="
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            if store.get("cierreDefinitivo"):
                continue

            item = Feature()
            item["ref"] = store["codtda"]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]

            municipio = store["municipio"]
            prefix = municipio + " - "
            if store["direccion"].startswith(prefix):
                item["street_address"] = store["direccion"][len(prefix) :]
            else:
                item["addr_full"] = store["direccion"]
            item["city"] = municipio
            item["state"] = STATE_CODES.get(store["comunidad"], store["comunidad"])
            item["country"] = "ES"

            item["website"] = response.urljoin(
                "/encuentra-tu-tienda/{}/{}/{}.html".format(
                    slugify_es(store["comunidad"]),
                    store["municipioFormateado"],
                    store["direccionFormateada"],
                )
            )

            item["opening_hours"] = self.parse_hours(store.get("horario"))

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

    def parse_hours(self, horario: str | None) -> OpeningHours:
        oh = OpeningHours()
        if not horario:
            return oh

        # Strip parenthetical asides, e.g. holiday exception notes, which
        # are not machine-parseable and don't affect the regular hours.
        horario = re.sub(r"\([^)]*\)", "", horario)

        for match in DAY_RANGE_RE.finditer(horario):
            days = DAY_RANGE_PHRASES[match.group(1)]
            for open_time, close_time in TIME_RANGE_RE.findall(match.group(2)):
                oh.add_days_range(days, open_time, close_time)

        return oh
