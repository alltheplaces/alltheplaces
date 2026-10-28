import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, OpeningHours
from locations.items import Feature

API_URL = "https://www.agenzie.generali.it/api/AgenzieApi/"


def title_case(value: str) -> str:
    # The source writes final accents as apostrophes ("LIBERTA'") and adds a space after elisions ("SANT' EFISIO").
    value = re.sub(r"\b([A-Z]{2,})([AEIOU])'", lambda m: m.group(1) + "ÀÈÌÒÙ"["AEIOU".index(m.group(2))], value.upper())
    value = re.sub(r"\b([A-Z]*[B-DF-HJ-NP-TV-Z])' ", r"\1'", value)
    # .title() lowercases Roman numerals ("Vittorio Emanuele Ii").
    return re.sub(r"\b[IVX]+\b", lambda m: m.group().upper(), value.title(), flags=re.IGNORECASE)


class GeneraliITSpider(Spider):
    name = "generali_it"
    item_attributes = {"brand": "Generali", "brand_wikidata": "Q670482", "name": "Generali"}
    allowed_domains = ["www.agenzie.generali.it"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The search returns agencies within a fixed 15 km radius; this ~25 km grid leaves only small coastal and border gaps.
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "IT"):
            yield JsonRequest(
                url=API_URL + "RicercaAgenzieByPosizione",
                data={"filtro": {"Latitudine": lat, "Longitudine": lon}, "includiPuntiVendita": False},
                callback=self.parse_search,
            )

    def parse_search(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        # Sales points ("punti vendita") are only searched within 5 km, so they are listed per parent agency.
        for agency in response.json():
            if code := agency.get("CodiceAgenzia"):
                yield JsonRequest(
                    url=API_URL + "RicercaAgenzieByCodiceAgenzia",
                    data={"codiceAgenzia": code, "includiPuntiVendita": True},
                )
        # Agencies whose per-code request fails (HTTP 500 for a few) still come from the search.
        yield from self.parse(response)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for agency in response.json():
            if not (ref := agency.get("CodiceNodo")):
                continue
            item = Feature()
            item["ref"] = ref
            item["lat"] = agency.get("Latitudine")
            item["lon"] = agency.get("Longitudine")
            # Sales points carry their parent agency's name and street in Titolo and Localizzazione, their own place in Ufficio.
            if agency.get("IsPuntoVendita"):
                branch = agency.get("Ufficio") or agency.get("Titolo") or ""
            else:
                branch = agency.get("Titolo") or ""
                # The street tells apart agencies sharing a Titolo; some Titoli already name it without its type.
                street = agency.get("Localizzazione") or ""
                if street.split(" ", 1)[-1].upper() not in branch.upper():
                    branch = f"{branch} {street}"
            item["branch"] = title_case(branch.strip())
            address = agency.get("Indirizzo") or ""
            if match := re.match(r"(.+), (\d{5}), (.+) \((\w+)\)$", address):
                item["street_address"] = title_case(match.group(1))
                item["postcode"] = match.group(2)
                # San Marino addresses give the country as city and "EE" (abroad) as province.
                if "SAN MARINO" in match.group(3):
                    item["country"] = "SM"
                else:
                    item["city"] = title_case(match.group(3))
                    item["state"] = match.group(4)
            else:
                item["addr_full"] = address
            item["phone"] = agency.get("Tel")
            item["website"] = agency.get("UrlSitoAgenziale")
            item["facebook"] = agency.get("UrlFacebook")
            if fax := agency.get("Fax"):
                item["extras"]["fax"] = fax
            apply_category(Categories.OFFICE_INSURANCE, item)

            # Half days read e.g. "MARMAT: MAT.CHIUSO/14:30-18:00" or "VEN: 09:00-13:00/POM.CHIUSO".
            hours = " ".join(
                f"{(entry.get('Giorni') or '').removesuffix('MAT')} {entry.get('Orari') or ''}"
                for entry in agency.get("OrariApertura") or []
            )
            hours = re.sub(r"(MAT|POM)\.CHIUSO", "", hours)
            # Some agencies list every day as closed, which means no hours are published.
            if re.search(r"\d\d:\d\d", hours):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(
                    hours, days=DAYS_IT, delimiters=DELIMITERS_IT, closed=CLOSED_IT
                )
            yield item
